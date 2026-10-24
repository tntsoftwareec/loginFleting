"""
Seed: 001_roles_seed.py
Crea los roles base del sistema (sin datos de demostración).
"""


def run(db):
    cursor = db.cursor()

    default_roles = [
        ("Admin", "Administrador con acceso total al sistema", 1, 1, 1, 1),
        ("Cajero", "Operador de punto de venta", 1, 1, 1, 0),
        ("Usuario", "Usuario estándar de solo lectura", 1, 0, 0, 0),
        ("Supervisor", "Supervisa las operaciones diarias", 1, 1, 1, 0),
        ("Gerente", "Gestión estratégica y reportes", 1, 1, 1, 1),
        ("Auditor", "Auditoría y control interno", 1, 0, 0, 0),
        ("Soporte", "Soporte técnico y asistencia", 1, 1, 1, 0),
    ]

    for name, desc, can_read, can_write, can_update, can_delete in default_roles:
        cursor.execute(
            """
            INSERT OR IGNORE INTO roles (name, description, can_read, can_write, can_update, can_delete)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, desc, can_read, can_write, can_update, can_delete)
        )

    db.commit()
