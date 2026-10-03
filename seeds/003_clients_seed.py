"""
Seed: 003_clients_seed.py
Seeds initial client records.
"""
from faker import Faker

fake = Faker('es_ES')
Faker.seed(101)

def run(db):
    cursor = db.cursor()

    default_clients = [
        ("CONSUMIDOR FINAL", "9999999999999", "CONSUMIDOR FINAL", "consumidor@mail.com", "0999999999", "Ciudad"),
        ("CEDULA", "1723456789", "Juan Carlos Pérez", "juan.perez@example.com", "0987654321", "Av. Amazonas y Colón, Quito"),
        ("RUC", "1792123456001", "Corporación Ecuador S.A.", "contacto@corpecuador.ec", "022345678", "Av. 10 de Agosto N34-12, Quito"),
        ("CEDULA", "0912345678", "María Fernanda López", "mlopez@example.com", "0991234567", "Urdesa Central Calle 2da, Guayaquil"),
        ("RUC", "0998765432001", "Comercializadora del Pacífico Cía. Ltda.", "facturas@pacificocomercial.ec", "042889900", "Av. Carlos Julio Arosemena Km 2.5, Guayaquil")
    ]

    for tipo, iden, razon, email, tel, dir in default_clients:
        cursor.execute(
            """
            INSERT OR IGNORE INTO clients (tipo_documento, identificacion, razon_social, email, telefono, direccion, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
            """,
            (tipo, iden, razon, email, tel, dir)
        )

    db.commit()
