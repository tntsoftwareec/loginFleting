from app.models.role_model import RoleModel
from app.models.user_model import UserModel

class RoleController:
    @classmethod
    def get_all(cls):
        """Retorna todos los roles con el conteo de usuarios asociados."""
        roles = RoleModel.all()
        result = []
        for r in roles:
            role_dict = r.copy() if isinstance(r, dict) else r.to_dict()
            users_count = len(UserModel.where(role_id=role_dict["id"]))
            role_dict["users_count"] = users_count
            result.append(role_dict)
        return result

    @classmethod
    def get_by_id(cls, role_id: int):
        """Retorna un rol por su ID."""
        return RoleModel.find(role_id)

    @classmethod
    def create(cls, name: str, description: str = "", can_read: int = 1, can_write: int = 1, can_update: int = 1, can_delete: int = 1):
        """Crea un nuevo rol tras validar unicidad de nombre y permisos.
        
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

        new_role = RoleModel.create(
            name=name,
            description=description,
            can_read=1 if can_read else 0,
            can_write=1 if can_write else 0,
            can_update=1 if can_update else 0,
            can_delete=1 if can_delete else 0,
        )
        return True, new_role

    @classmethod
    def update(cls, role_id: int, name: str, description: str = "", can_read: int = 1, can_write: int = 1, can_update: int = 1, can_delete: int = 1):
        """Actualiza un rol existente con sus permisos.
        
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

        updated_role = RoleModel.update_by_id(
            role_id,
            name=name,
            description=description,
            can_read=1 if can_read else 0,
            can_write=1 if can_write else 0,
            can_update=1 if can_update else 0,
            can_delete=1 if can_delete else 0,
        )
        return True, updated_role

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
            return False, f"No se puede eliminar el rol '{role['name']}' porque tiene {len(assigned_users)} usuario(s) asignado(s)."

        RoleModel.delete_by_id(role_id)
        return True, "Rol eliminado exitosamente."
