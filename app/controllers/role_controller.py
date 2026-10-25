from core.database import get_connection, transaction
from core.permissions import (
    MODULE_KEYS,
    legacy_flags_from_permissions,
    normalize_permissions,
    permissions_from_legacy,
)
from core.state import AppState
from app.models.role_model import RoleModel
from app.models.role_permission_model import RolePermissionModel
from app.models.user_model import UserModel


class RoleController:
    @classmethod
    def get_permissions(cls, role_id: int):
        """Devuelve la matriz completa de permisos de un rol.

        Siempre incluye todos los módulos del catálogo; los que no tengan
        fila en la base se devuelven en False.
        """
        rows = RolePermissionModel.where(role_id=role_id)
        raw = {}
        for row in rows:
            raw[row["module"]] = {
                "can_read": bool(row.get("can_read")),
                "can_write": bool(row.get("can_write")),
                "can_update": bool(row.get("can_update")),
                "can_delete": bool(row.get("can_delete")),
            }
        return normalize_permissions(raw)

    @classmethod
    def _replace_permissions(cls, role_id: int, permissions: dict):
        """Reemplaza las filas de permisos. Debe ejecutarse en una transacción."""
        conn = get_connection()
        conn.execute(
            "DELETE FROM role_permissions WHERE role_id = ?",
            (role_id,),
        )
        for module in MODULE_KEYS:
            perms = permissions.get(module, {})
            conn.execute(
                """
                INSERT INTO role_permissions
                    (role_id, module, can_read, can_write, can_update, can_delete)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    role_id,
                    module,
                    1 if perms.get("can_read") else 0,
                    1 if perms.get("can_write") else 0,
                    1 if perms.get("can_update") else 0,
                    1 if perms.get("can_delete") else 0,
                ),
            )

    @classmethod
    def set_permissions(cls, role_id: int, permissions: dict):
        """Guarda la matriz de permisos de un rol."""
        normalized = normalize_permissions(permissions)
        with transaction():
            cls._replace_permissions(role_id, normalized)
        return normalized

    @classmethod
    def get_all(cls):
        """Retorna todos los roles con usuarios y permisos por módulo."""
        roles = RoleModel.all()
        result = []
        for r in roles:
            role_dict = r.copy() if isinstance(r, dict) else r.to_dict()
            users_count = len(UserModel.where(role_id=role_dict["id"]))
            role_dict["users_count"] = users_count
            role_dict["module_permissions"] = cls.get_permissions(role_dict["id"])
            role_dict["allowed_modules"] = [
                key
                for key, perms in role_dict["module_permissions"].items()
                if perms.get("can_read")
            ]
            result.append(role_dict)
        return result

    @classmethod
    def get_by_id(cls, role_id: int):
        """Retorna un rol por su ID, incluyendo sus permisos por módulo."""
        role = RoleModel.find(role_id)
        if role:
            role["module_permissions"] = cls.get_permissions(role_id)
            role["allowed_modules"] = [
                key
                for key, perms in role["module_permissions"].items()
                if perms.get("can_read")
            ]
        return role

    @classmethod
    def create(
        cls,
        name: str,
        description: str = "",
        can_read: int = 1,
        can_write: int = 1,
        can_update: int = 1,
        can_delete: int = 1,
        permissions: dict | None = None,
    ):
        """Crea un nuevo rol con permisos por módulo.

        ``permissions`` es la matriz módulo -> acciones. Si se omite, se
        conservan los flags globales heredados aplicados a todos los módulos.

        Returns:
            (success: bool, data_or_error: dict|str)
        """
        name = (name or "").strip()
        description = (description or "").strip()
        if not name:
            return False, "El nombre del rol es requerido."

        existing = RoleModel.where(name=name)
        if existing:
            return False, f"Ya existe un rol con el nombre '{name}'."

        if permissions is None:
            normalized = permissions_from_legacy(
                can_read, can_write, can_update, can_delete
            )
        else:
            normalized = normalize_permissions(permissions)

        if not any(perms.get("can_read") for perms in normalized.values()):
            return False, "El rol debe tener acceso de lectura a al menos un módulo."

        flags = legacy_flags_from_permissions(normalized)
        with transaction():
            new_role = RoleModel.create(
                name=name,
                description=description,
                can_read=flags[0],
                can_write=flags[1],
                can_update=flags[2],
                can_delete=flags[3],
            )
            cls._replace_permissions(new_role["id"], normalized)

        return True, cls.get_by_id(new_role["id"])

    @classmethod
    def update(
        cls,
        role_id: int,
        name: str,
        description: str = "",
        can_read: int = 1,
        can_write: int = 1,
        can_update: int = 1,
        can_delete: int = 1,
        permissions: dict | None = None,
    ):
        """Actualiza un rol y, opcionalmente, su matriz de permisos.

        Si ``permissions`` es ``None`` se conservan los permisos por módulo
        existentes y solo se actualizan los datos globales del rol.

        Returns:
            (success: bool, data_or_error: dict|str)
        """
        name = (name or "").strip()
        description = (description or "").strip()
        if not name:
            return False, "El nombre del rol es requerido."

        role = RoleModel.find(role_id)
        if not role:
            return False, "Rol no encontrado."

        existing = RoleModel.where(name=name)
        if existing and int(existing[0]["id"]) != int(role_id):
            return False, f"Ya existe otro rol con el nombre '{name}'."

        if permissions is None:
            flags = (
                1 if can_read else 0,
                1 if can_write else 0,
                1 if can_update else 0,
                1 if can_delete else 0,
            )
            normalized = None
        else:
            normalized = normalize_permissions(permissions)
            if not any(perms.get("can_read") for perms in normalized.values()):
                return False, "El rol debe tener acceso de lectura a al menos un módulo."

            # Evita que el usuario en sesión se quite a sí mismo el acceso a
            # la administración de roles y no pueda revertir el cambio.
            current_role_id = (AppState.current_user or {}).get("role_id")
            if current_role_id and int(current_role_id) == int(role_id):
                current_permissions = cls.get_permissions(role_id)
                current_roles = current_permissions.get("roles", {})
                new_roles = normalized.get("roles", {})
                for action in ("can_read", "can_update"):
                    if current_roles.get(action) and not new_roles.get(action):
                        return False, (
                            "No puedes quitarte a ti mismo el acceso a Roles "
                            "y permisos."
                        )

            flags = legacy_flags_from_permissions(normalized)

        with transaction():
            RoleModel.update_by_id(
                role_id,
                name=name,
                description=description,
                can_read=flags[0],
                can_write=flags[1],
                can_update=flags[2],
                can_delete=flags[3],
            )
            if normalized is not None:
                cls._replace_permissions(role_id, normalized)

        return True, cls.get_by_id(role_id)

    @classmethod
    def delete(cls, role_id: int):
        """Elimina un rol si no tiene usuarios asignados.

        Returns:
            (success: bool, message: str)
        """
        role = RoleModel.find(role_id)
        if not role:
            return False, "Rol no encontrado."

        assigned_users = UserModel.where(role_id=role_id)
        if assigned_users:
            role_name = role["name"]
            return False, (
                f"No se puede eliminar el rol '{role_name}' porque tiene "
                f"{len(assigned_users)} usuario(s) asignado(s)."
            )

        with transaction():
            conn = get_connection()
            conn.execute(
                "DELETE FROM role_permissions WHERE role_id = ?",
                (role_id,),
            )
            RoleModel.delete_by_id(role_id)

        return True, "Rol eliminado exitosamente."
