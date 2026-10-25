"""
Seed: 007_advanced_roles_seed.py
Aplica permisos por módulo a los roles base y crea los roles de ejemplo
"Vendedor" y "Bodeguero" cuando no existan.

Los roles personalizados que no aparecen en ``DEFAULT_ROLE_PRESETS``
conservan los permisos heredados de sus flags globales.
"""

from core.permissions import (
    DEFAULT_ROLE_PRESETS,
    PRESETS,
    MODULE_KEYS,
    legacy_flags_from_permissions,
    permissions_from_legacy,
    preset_permissions,
)


def _set_permissions(db, role_id: int, permissions: dict):
    db.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))
    for module in MODULE_KEYS:
        perms = permissions.get(module, {})
        db.execute(
            """
            INSERT INTO role_permissions
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


def _create_example_role(db, preset_key: str) -> int:
    preset = PRESETS[preset_key]
    permissions = preset_permissions(preset_key)
    can_read, can_write, can_update, can_delete = legacy_flags_from_permissions(
        permissions
    )
    db.execute(
        """
        INSERT INTO roles
            (name, description, can_read, can_write, can_update, can_delete)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            preset["label"],
            preset["description"],
            can_read,
            can_write,
            can_update,
            can_delete,
        ),
    )
    role_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    _set_permissions(db, role_id, permissions)
    return role_id


def run(db):
    # En una base nueva las migraciones corren antes que los seeds, así que
    # la tabla existe pero los roles recién se crean en el seed 001.
    roles = db.execute("SELECT id, name FROM roles").fetchall()
    by_lower = {(name or "").strip().lower(): role_id for role_id, name in roles}

    # Roles de ejemplo solicitados por el negocio. Si ya existe "vendedor"
    # (en cualquier combinación de mayúsculas), se reutiliza y se le aplica
    # el preset en lugar de crear un duplicado.
    for preset_key in ("vendedor", "bodeguero"):
        if preset_key not in by_lower:
            role_id = _create_example_role(db, preset_key)
            by_lower[preset_key] = role_id

    # Aplicar presets a los roles base conocidos.
    roles = db.execute("SELECT id, name FROM roles").fetchall()
    for role_id, name in roles:
        preset_key = DEFAULT_ROLE_PRESETS.get((name or "").strip().lower())
        if preset_key:
            _set_permissions(db, role_id, preset_permissions(preset_key))
            continue

        # Roles personalizados: si la migración no encontró permisos (por
        # ejemplo, una base creada antes de esta funcionalidad), se heredan
        # los flags globales.
        count = db.execute(
            "SELECT COUNT(*) FROM role_permissions WHERE role_id = ?",
            (role_id,),
        ).fetchone()[0]
        if count == 0:
            legacy = db.execute(
                """
                SELECT can_read, can_write, can_update, can_delete
                FROM roles WHERE id = ?
                """,
                (role_id,),
            ).fetchone()
            _set_permissions(db, role_id, permissions_from_legacy(*legacy))

    db.commit()
