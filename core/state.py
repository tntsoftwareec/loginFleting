
class AppState:
    device = None  # mobile | tablet | desktop
    language = "es"
    theme_mode = "system"  # light | dark | system
    current_route = "/"
    current_user = None  # dict con email, role, name, permissions al autenticar
    # Ítems que se preseleccionan al abrir el POS o una nueva cotización
    # (por ejemplo, al pulsar "Facturar" en el catálogo de servicios).
    pending_cart_items = None

    @classmethod
    def has_permission(cls, perm_key: str) -> bool:
        """Verifica si el usuario autenticado tiene el permiso indicado.

        Falla de forma segura: sin sesión o sin permisos definidos se deniega
        el acceso. El Router además redirige al login en rutas protegidas.
        """
        if not cls.current_user:
            return False
        perms = cls.current_user.get("permissions")
        if not perms or not isinstance(perms, dict):
            return False
        return bool(perms.get(perm_key, False))
