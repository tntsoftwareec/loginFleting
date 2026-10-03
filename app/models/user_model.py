import hashlib
from core.base_model import BaseModel
from core.orm import ForeignKey

class UserModel(BaseModel):
    table_name = "users"
    role = ForeignKey("roles", "role_id")

    @staticmethod
    def hash_password(password: str) -> str:
        if not password:
            return ""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @classmethod
    def authenticate(cls, email: str, password: str):
        users = cls.where(email=email.strip().lower())
        if not users:
            return None
        
        user = users[0]
        hashed_input = cls.hash_password(password)

        # Allow plain match (for legacy demo) or sha256 match
        if user["password"] in (password, hashed_input):
            from app.models.role_model import RoleModel
            role_id = user.get("role_id")
            role_obj = RoleModel.find(role_id) if role_id else None
            role_name = role_obj["name"] if role_obj else "Sin Rol"

            permissions = {
                "can_read": bool(role_obj.get("can_read", 1)) if role_obj else True,
                "can_write": bool(role_obj.get("can_write", 1)) if role_obj else True,
                "can_update": bool(role_obj.get("can_update", 1)) if role_obj else True,
                "can_delete": bool(role_obj.get("can_delete", 1)) if role_obj else True,
            }

            return {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role_id": user["role_id"],
                "role": role_name,
                "permissions": permissions,
                "status": user.get("status", "active")
            }
        return None
