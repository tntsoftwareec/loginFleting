"""
Seed: 004_suppliers_seed.py
Seeds initial supplier records.
"""

def run(db):
    cursor = db.cursor()

    default_suppliers = [
        ("RUC", "1790011223001", "Distribuidora Nacional de Suministros S.A.", "ventas@dinasum.ec", "022554433", "Av. Galo Plaza Lasso N55-12, Quito", "Ing. Roberto Gómez"),
        ("RUC", "1791122334001", "Importadora Tecnológica del Ecuador", "soporte@importec.ec", "022998877", "Av. Eloy Alfaro y Rep. del Salvador, Quito", "Lcda. Andrea Ruiz"),
        ("RUC", "0991122334001", "Servicios Logísticos y Transporte Cía. Ltda.", "operaciones@servilog.ec", "042112233", "Vía a Daule Km 10.5, Guayaquil", "Carlos Andrade")
    ]

    for tipo, iden, razon, email, tel, dir, contacto in default_suppliers:
        cursor.execute(
            """
            INSERT OR IGNORE INTO suppliers (tipo_documento, identificacion, razon_social, email, telefono, direccion, contacto, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
            """,
            (tipo, iden, razon, email, tel, dir, contacto)
        )

    db.commit()
