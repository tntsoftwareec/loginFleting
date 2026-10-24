"""
Seed: 003_clients_seed.py
Crea únicamente el cliente genérico "CONSUMIDOR FINAL".
No se cargan clientes de demostración.
"""


def run(db):
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO clients (
            tipo_documento, identificacion, razon_social, email, telefono, direccion, status
        )
        VALUES (?, ?, ?, ?, ?, ?, 'active')
        """,
        (
            "CONSUMIDOR FINAL",
            "9999999999999",
            "CONSUMIDOR FINAL",
            "consumidor@mail.com",
            "",
            "",
        ),
    )

    db.commit()
