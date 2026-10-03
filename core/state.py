
class AppState:
    device = None  # mobile | tablet | desktop
    initial_device = "mobile"
    language = "pt"
    initialized = False
    current_route = "/"
    current_user = None  # dict con email, role, name, permissions al autenticar

    @classmethod
    def has_permission(cls, perm_key: str) -> bool:
        """Verifica si el usuario autenticado tiene el permiso indicado."""
        if not cls.current_user:
            return True
        perms = cls.current_user.get("permissions")
        if not perms or not isinstance(perms, dict):
            return True
        return bool(perms.get(perm_key, True))
