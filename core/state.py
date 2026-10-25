
class AppState:
    device = None  # mobile | tablet | desktop
    language = "es"
    theme_mode = "system"  # light | dark | system
    current_route = "/"
    # dict con email, role, name, permissions (globales heredados) y
    # module_permissions (matriz por módulo) al autenticar.
    current_user = None
    # Ítems que se preseleccionan al abrir el POS o una nueva cotización
    # (por ejemplo, al pulsar "Facturar" en el catálogo de servicios).
    pending_cart_items = None

    @classmethod
    def has_permission(cls, perm_key: str, module: str | None = None) -> bool:
        """Verifica si el usuario autenticado tiene el permiso indicado.

        - Con ``module`` se consulta la matriz ``module_permissions``.
        - Sin ``module`` se consulta el permiso global heredado.
        - Si no hay matriz por módulo (sesiones antiguas o pruebas), se usa
          el permiso global como respaldo.

        Falla de forma segura: sin sesión o sin permisos definidos se deniega
        el acceso. El Router además redirige al login en rutas protegidas.
        """
        if not cls.current_user:
            return False

        if module:
            module_permissions = cls.current_user.get("module_permissions")
            if isinstance(module_permissions, dict):
                perms = module_permissions.get(module)
                if not isinstance(perms, dict):
                    return False
                return bool(perms.get(perm_key, False))

        perms = cls.current_user.get("permissions")
        if not perms or not isinstance(perms, dict):
            return False
        return bool(perms.get(perm_key, False))

    @classmethod
    def can_access_module(cls, module: str) -> bool:
        """Atajo para verificar el permiso de lectura de un módulo."""
        return cls.has_permission("can_read", module)
