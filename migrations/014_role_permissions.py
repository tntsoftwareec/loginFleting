"""
Migration: 014_role_permissions.py
Crea la tabla de permisos por módulo y migra los permisos globales existentes.

Cada fila de ``role_permissions`` representa el acceso de un rol a un módulo
concreto (POS, clientes, inventario, etc.). Las columnas globales de ``roles``
se mantienen por compatibilidad, pero el control de acceso usa esta tabla.
"""

from core.permissions import (
    DEFAULT_ROLE_PRESETS,
    MODULE_KEYS,
    permissions_from_legacy,
    preset_permissions,
)


def _insert_permissions(db, role_id: int, permissions: dict):
    for module in MODULE_KEYS:
        perms = permissions.get(module, {})
        db.execute(
            """
            INSERT OR IGNORE INTO role_permissions
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


def up(db):
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS role_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER NOT NULL,
            module TEXT NOT NULL,
            can_read INTEGER DEFAULT 0,
            can_write INTEGER DEFAULT 0,
            can_update INTEGER DEFAULT 0,
            can_delete INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (role_id, module),
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
        )
        """
    )
    db.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_role_permissions_role_module
        ON role_permissions (role_id, module)
        """
    )

    # En una base existente los roles ya existen y heredan sus flags globales.
    # En una base nueva la tabla está vacía: el seed 007 aplica los presets.
    roles = db.execute(
        """
        SELECT id, name, can_read, can_write, can_update, can_delete
        FROM roles
        """
    ).fetchall()

    for role_id, name, can_read, can_write, can_update, can_delete in roles:
        preset_key = DEFAULT_ROLE_PRESETS.get((name or "").strip().lower())
        if preset_key:
            permissions = preset_permissions(preset_key)
        else:
            permissions = permissions_from_legacy(
                can_read, can_write, can_update, can_delete
            )
        _insert_permissions(db, role_id, permissions)

    db.commit()


def down(db):
    db.execute("DROP INDEX IF EXISTS idx_role_permissions_role_module")
    db.execute("DROP TABLE IF EXISTS role_permissions")
    db.commit()
