"""Catálogo de módulos y permisos por módulo.

Cada módulo de la aplicación (POS, clientes, inventario, etc.) tiene su
propio conjunto de permisos CRUD. Esto permite que un rol pueda acceder
solamente a los módulos que necesita; por ejemplo, un vendedor puede tener
acceso a POS y clientes, mientras que un bodeguero solo a inventario.

El catálogo es la fuente de verdad para:

- Las migraciones y seeds que crean la tabla ``role_permissions``.
- El router y el menú, que ocultan rutas sin permiso de lectura.
- La vista de roles, que dibuja la matriz de permisos.
- Los controladores, que normalizan y validan lo que se guarda.
"""

from __future__ import annotations

ACTION_ORDER = ("can_read", "can_write", "can_update", "can_delete")

ACTION_LABELS = {
    "can_read": "Ver",
    "can_write": "Crear",
    "can_update": "Editar",
    "can_delete": "Eliminar",
}

ACTION_ICONS = {
    "can_read": "VISIBILITY_ROUNDED",
    "can_write": "ADD_CIRCLE_OUTLINE_ROUNDED",
    "can_update": "EDIT_ROUNDED",
    "can_delete": "DELETE_FOREVER_ROUNDED",
}

ACTION_COLORS = {
    "can_read": "SUCCESS",
    "can_write": "INDIGO",
    "can_update": "AMBER",
    "can_delete": "DANGER",
}

# Orden intencional: es el que se muestra en la matriz de permisos y en los
# resúmenes de cada rol. Las acciones disponibles dependen del módulo.
MODULES = [
    {
        "key": "home",
        "label": "Inicio",
        "description": "Panel principal y accesos rápidos",
        "route": "/",
        "icon": "HOME",
        "actions": ("can_read",),
    },
    {
        "key": "pos",
        "label": "Punto de Venta",
        "description": "Facturación rápida en caja",
        "route": "/pos",
        "icon": "POINT_OF_SALE_ROUNDED",
        "actions": ("can_read", "can_write"),
    },
    {
        "key": "invoices",
        "label": "Facturas",
        "description": "Consulta, envío al SRI y reenvío de comprobantes",
        "route": "/invoices",
        "icon": "RECEIPT_LONG_ROUNDED",
        "actions": ("can_read", "can_write", "can_update"),
    },
    {
        "key": "quotations",
        "label": "Cotizaciones",
        "description": "Creación, envío y facturación de cotizaciones",
        "route": "/quotations",
        "icon": "DESCRIPTION_ROUNDED",
        "actions": ("can_read", "can_write", "can_update", "can_delete"),
    },
    {
        "key": "clients",
        "label": "Clientes",
        "description": "Directorio y datos de facturación de clientes",
        "route": "/clients",
        "icon": "PEOPLE_ROUNDED",
        "actions": ("can_read", "can_write", "can_update", "can_delete"),
    },
    {
        "key": "suppliers",
        "label": "Proveedores",
        "description": "Directorio de proveedores y contactos",
        "route": "/suppliers",
        "icon": "LOCAL_SHIPPING_ROUNDED",
        "actions": ("can_read", "can_write", "can_update", "can_delete"),
    },
    {
        "key": "products",
        "label": "Productos",
        "description": "Catálogo de productos, precios e imágenes",
        "route": "/products",
        "icon": "INVENTORY_2_ROUNDED",
        "actions": ("can_read", "can_write", "can_update", "can_delete"),
    },
    {
        "key": "inventory",
        "label": "Inventario",
        "description": "Existencias, entradas, salidas y ajustes",
        "route": "/inventory",
        "icon": "WAREHOUSE_ROUNDED",
        "actions": ("can_read", "can_write", "can_update"),
    },
    {
        "key": "services",
        "label": "Servicios",
        "description": "Catálogo de servicios y tarifas",
        "route": "/services",
        "icon": "MISCELLANEOUS_SERVICES_ROUNDED",
        "actions": ("can_read", "can_write", "can_update", "can_delete"),
    },
    {
        "key": "company",
        "label": "Empresa",
        "description": "Datos del negocio, firma electrónica y SMTP",
        "route": "/company",
        "icon": "BUSINESS_ROUNDED",
        "actions": ("can_read", "can_update"),
    },
    {
        "key": "users",
        "label": "Usuarios",
        "description": "Altas, bajas y edición de usuarios",
        "route": "/users",
        "icon": "SUPERVISED_USER_CIRCLE_ROUNDED",
        "actions": ("can_read", "can_write", "can_update", "can_delete"),
    },
    {
        "key": "roles",
        "label": "Roles y permisos",
        "description": "Configuración de roles y acceso por módulo",
        "route": "/roles",
        "icon": "ADMIN_PANEL_SETTINGS_ROUNDED",
        "actions": ("can_read", "can_write", "can_update", "can_delete"),
    },
    {
        "key": "settings",
        "label": "Ajustes",
        "description": "Preferencias de tema e idioma",
        "route": "/settings",
        "icon": "SETTINGS",
        "actions": ("can_read", "can_update"),
    },
    {
        "key": "help",
        "label": "Ayuda",
        "description": "Documentación y soporte",
        "route": "/help",
        "icon": "HELP",
        "actions": ("can_read",),
    },
]

MODULE_KEYS = tuple(module["key"] for module in MODULES)
MODULES_BY_KEY = {module["key"]: module for module in MODULES}

# Acciones que se usan con frecuencia al definir presets.
_READ = ("can_read",)
_WRITE = ("can_read", "can_write")
_EDIT = ("can_read", "can_write", "can_update")
_FULL = ACTION_ORDER

# Presets que la vista de roles ofrece como punto de partida. No son
# obligatorios: el administrador puede marcar cualquier combinación.
PRESETS = {
    "administrador": {
        "label": "Administrador",
        "description": "Acceso total a todos los módulos",
        "grants": {key: _FULL for key in MODULE_KEYS},
    },
    "vendedor": {
        "label": "Vendedor",
        "description": "Factura en POS y registra clientes",
        "grants": {
            "pos": _WRITE,
            "clients": _EDIT,
        },
    },
    "bodeguero": {
        "label": "Bodeguero",
        "description": "Solo inventario y movimientos de stock",
        "grants": {
            "inventory": _EDIT,
        },
    },
    "cajero": {
        "label": "Cajero",
        "description": "POS, facturas, cotizaciones y clientes",
        "grants": {
            "home": _READ,
            "pos": _WRITE,
            "invoices": _WRITE,
            "quotations": _WRITE,
            "clients": _EDIT,
            "products": _READ,
            "services": _READ,
            "inventory": _READ,
            "help": _READ,
        },
    },
    "supervisor": {
        "label": "Supervisor",
        "description": "Operación completa y consulta administrativa",
        "grants": {
            "home": _READ,
            "pos": _WRITE,
            "invoices": _EDIT,
            "quotations": _EDIT,
            "clients": _EDIT,
            "suppliers": _EDIT,
            "products": _EDIT,
            "inventory": _EDIT,
            "services": _EDIT,
            "company": _READ,
            "users": _READ,
            "roles": _READ,
            "settings": _READ,
            "help": _READ,
        },
    },
    "usuario": {
        "label": "Usuario",
        "description": "Consulta operativa sin edición",
        "grants": {
            "home": _READ,
            "pos": _READ,
            "invoices": _READ,
            "quotations": _READ,
            "clients": _READ,
            "products": _READ,
            "inventory": _READ,
            "services": _READ,
            "help": _READ,
        },
    },
    "auditor": {
        "label": "Auditor",
        "description": "Lectura de todos los módulos para auditoría",
        "grants": {key: _READ for key in MODULE_KEYS},
    },
    "soporte": {
        "label": "Soporte",
        "description": "Soporte técnico con acceso a datos maestros",
        "grants": {
            "home": _READ,
            "clients": _EDIT,
            "suppliers": _READ,
            "products": _EDIT,
            "inventory": _READ,
            "services": _EDIT,
            "company": _READ,
            "users": _EDIT,
            "roles": _READ,
            "settings": _READ,
            "help": _READ,
        },
    },
    "solo_lectura": {
        "label": "Solo lectura",
        "description": "Consulta todos los módulos sin modificarlos",
        "grants": {key: _READ for key in MODULE_KEYS},
    },
}

# Presets sugeridos para los roles base. Los roles personalizados conservan
# los permisos globales heredados al migrar.
DEFAULT_ROLE_PRESETS = {
    "admin": "administrador",
    "gerente": "administrador",
    "supervisor": "supervisor",
    "cajero": "cajero",
    "vendedor": "vendedor",
    "bodeguero": "bodeguero",
    "usuario": "usuario",
    "auditor": "auditor",
    "soporte": "soporte",
}

# Orden de los botones de preset en la interfaz.
PRESET_ORDER = (
    "vendedor",
    "bodeguero",
    "cajero",
    "supervisor",
    "solo_lectura",
    "administrador",
)


def empty_permissions() -> dict[str, dict[str, bool]]:
    """Devuelve la matriz completa con todos los permisos en False."""
    return {
        module["key"]: {action: False for action in module["actions"]}
        for module in MODULES
    }


def normalize_permissions(permissions) -> dict[str, dict[str, bool]]:
    """Limpia una matriz de permisos y la limita al catálogo de módulos.

    - Ignora módulos o acciones desconocidas.
    - Fuerza ``can_read`` cuando se concede cualquier otra acción, para que
      un permiso de escritura nunca quede inaccesible desde la interfaz.
    """
    result = empty_permissions()
    if not isinstance(permissions, dict):
        return result

    for module in MODULES:
        key = module["key"]
        raw = permissions.get(key)
        if not isinstance(raw, dict):
            raw = {}
        normalized = {
            action: bool(raw.get(action, False))
            for action in module["actions"]
        }
        if any(
            value
            for action, value in normalized.items()
            if action != "can_read"
        ):
            normalized["can_read"] = True
        result[key] = normalized

    return result


def permissions_from_legacy(
    can_read=1,
    can_write=1,
    can_update=1,
    can_delete=1,
) -> dict[str, dict[str, bool]]:
    """Convierte los antiguos permisos globales a la matriz por módulo."""
    flags = {
        "can_read": bool(can_read),
        "can_write": bool(can_write),
        "can_update": bool(can_update),
        "can_delete": bool(can_delete),
    }
    return normalize_permissions(
        {key: flags.copy() for key in MODULE_KEYS}
    )


def preset_permissions(preset_key: str) -> dict[str, dict[str, bool]]:
    """Devuelve la matriz de permisos de un preset (o todo en False)."""
    preset = PRESETS.get(preset_key)
    if not preset:
        return empty_permissions()

    grants = preset.get("grants", {})
    raw = {
        key: {action: action in actions for action in ACTION_ORDER}
        for key, actions in grants.items()
    }
    return normalize_permissions(raw)


def legacy_flags_from_permissions(permissions) -> tuple[int, int, int, int]:
    """Resume la matriz en los cuatro flags globales de la tabla ``roles``.

    Las columnas globales se conservan por compatibilidad, pero la fuente de
    verdad para el control de acceso es ``role_permissions``.
    """
    normalized = normalize_permissions(permissions)
    flags = []
    for action in ACTION_ORDER:
        flags.append(
            1
            if any(
                module_perms.get(action, False)
                for module_perms in normalized.values()
            )
            else 0
        )
    return tuple(flags)


def allowed_modules(permissions) -> list[str]:
    """Lista de claves de módulos con permiso de lectura."""
    normalized = normalize_permissions(permissions)
    return [
        key
        for key in MODULE_KEYS
        if normalized.get(key, {}).get("can_read", False)
    ]
