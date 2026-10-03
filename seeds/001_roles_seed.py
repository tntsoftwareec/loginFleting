"""
Seed: 001_roles_seed.py
Seeds roles using default permissions and Faker for descriptions and role variations.
"""
from faker import Faker

fake = Faker('es_ES')
Faker.seed(42)

def run(db):
    cursor = db.cursor()
    
    # Core system roles
    default_roles = [
        ("Admin", "Administrador con acceso total al sistema", 1, 1, 1, 1),
        ("Cajero", "Operador de punto de venta (crea y edita)", 1, 1, 1, 0),
        ("Usuario", "Usuario estándar (solo lectura)", 1, 0, 0, 0),
        ("Supervisor", f"Supervisa las operaciones diarias: {fake.catch_phrase()}", 1, 1, 1, 0),
        ("Gerente", f"Gestión estratégica y reportes: {fake.bs()}", 1, 1, 1, 1),
        ("Auditor", f"Auditoría y control interno: {fake.sentence()}", 1, 0, 0, 0),
        ("Soporte", f"Soporte técnico y asistencia: {fake.sentence()}", 1, 1, 1, 0),
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
