import re
from app.models.user_model import UserModel
from app.models.role_model import RoleModel

class UserController:
    @classmethod
    def get_all(cls):
        """Retorna todos los usuarios con información del rol asociado."""
        users = UserModel.with_("role").all()
        result = []
        for u in users:
            u_dict = u.copy() if isinstance(u, dict) else u.to_dict()
            role_info = u_dict.get("role")
            if isinstance(role_info, dict):
                u_dict["role_name"] = role_info.get("name", "Sin Rol")
            else:
                role_id = u_dict.get("role_id")
                role_obj = RoleModel.find(role_id) if role_id else None
                u_dict["role_name"] = role_obj["name"] if role_obj else "Sin Rol"
            result.append(u_dict)
        return result

    @classmethod
    def get_by_id(cls, user_id: int):
        """Retorna un usuario por ID."""
        return UserModel.find(user_id)

    @classmethod
    def create(cls, name: str, email: str, password: str, role_id: int, status: str = "active"):
        """Crea un nuevo usuario tras validar datos y contraseña.
        
        Returns:
            (success: bool, data_or_error: dict|str)
        """
        name = (name or "").strip()
        email = (email or "").strip().lower()
        password = (password or "").strip()

        if not name:
            return False, "El nombre del usuario es requerido."
        if not email:
            return False, "El correo electrónico es requerido."
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            return False, "Formato de correo electrónico inválido."
        if not password:
            return False, "La contraseña es requerida."
        if len(password) < 6:
            return False, "La contraseña debe tener al menos 6 caracteres."
        if not role_id:
            return False, "Debe seleccionar un rol."

        try:
            role_id_int = int(role_id)
        except (ValueError, TypeError):
            return False, "El rol seleccionado es inválido."

        role = RoleModel.find(role_id_int)
        if not role:
            return False, "El rol seleccionado no existe."

        existing = UserModel.where(email=email)
        if existing:
            return False, f"Ya existe un usuario registrado con el correo '{email}'."

        hashed_pass = UserModel.hash_password(password)

        new_user = UserModel.create(
            name=name,
            email=email,
            password=hashed_pass,
            role_id=role_id_int,
            status=status if status in ("active", "inactive") else "active"
        )
        return True, new_user

    @classmethod
    def update(cls, user_id: int, name: str, email: str, role_id: int, status: str = "active", password: str = None):
        """Actualiza un usuario existente.
        
        Returns:
            (success: bool, data_or_error: dict|str)
        """
        name = (name or "").strip()
        email = (email or "").strip().lower()

        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            return False, "ID de usuario inválido."

        user = UserModel.find(user_id_int)
        if not user:
            return False, "Usuario no encontrado."

        if not name:
            return False, "El nombre del usuario es requerido."
        if not email:
            return False, "El correo electrónico es requerido."
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            return False, "Formato de correo electrónico inválido."

        if not role_id:
            return False, "Debe seleccionar un rol."

        try:
            role_id_int = int(role_id)
        except (ValueError, TypeError):
            return False, "El rol seleccionado es inválido."

        role = RoleModel.find(role_id_int)
        if not role:
            return False, "El rol seleccionado no existe."

        existing = UserModel.where(email=email)
        if existing and int(existing[0]["id"]) != user_id_int:
            return False, f"Ya existe otro usuario registrado con el correo '{email}'."

        update_data = {
            "name": name,
            "email": email,
            "role_id": role_id_int,
            "status": status if status in ("active", "inactive") else "active"
        }

        if password is not None:
            pass_str = str(password).strip()
            if len(pass_str) > 0:
                if len(pass_str) < 6:
                    return False, "La nueva contraseña debe tener al menos 6 caracteres."
                update_data["password"] = UserModel.hash_password(pass_str)

        updated_user = UserModel.update_by_id(user_id_int, **update_data)
        return True, updated_user

    @classmethod
    def delete(cls, user_id: int):
        """Elimina un usuario por ID.
        
        Returns:
            (success: bool, message: str)
        """
        user = UserModel.find(user_id)
        if not user:
            return False, "Usuario no encontrado."

        UserModel.delete_by_id(user_id)
        return True, "Usuario eliminado exitosamente."
