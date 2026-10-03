from core.base_model import BaseModel
from core.orm import HasMany

class RoleModel(BaseModel):
    table_name = "roles"
    users = HasMany("users", "role_id")
