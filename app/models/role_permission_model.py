from core.base_model import BaseModel


class RolePermissionModel(BaseModel):
    """Permisos CRUD de un rol para un módulo concreto."""

    table_name = "role_permissions"
