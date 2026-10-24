"""
Migration: 012_sri_and_product_supplier.py
Agrega el proveedor de los productos y los datos de respuesta del SRI en facturas.
"""


def up(db):
    cursor = db.cursor()

    # Proveedor opcional del producto.
    product_columns = {
        row[1] for row in cursor.execute("PRAGMA table_info(products)").fetchall()
    }
    if "supplier_id" not in product_columns:
        cursor.execute("ALTER TABLE products ADD COLUMN supplier_id INTEGER")

    # Datos del envío/recepción/autorización del SRI.
    invoice_columns = {
        row[1] for row in cursor.execute("PRAGMA table_info(invoices)").fetchall()
    }
    new_invoice_columns = {
        "email_estado": "TEXT DEFAULT ''",
        "sri_respuesta": "TEXT DEFAULT ''",
        "sri_autorizacion": "TEXT DEFAULT ''",
        "sri_fecha_autorizacion": "TEXT DEFAULT ''",
        "sri_fecha_envio": "TEXT DEFAULT ''",
    }
    for column, definition in new_invoice_columns.items():
        if column not in invoice_columns:
            cursor.execute(
                f"ALTER TABLE invoices ADD COLUMN {column} {definition}"
            )

    db.commit()


def down(db):
    # SQLite no elimina columnas de forma portable en todas las versiones.
    pass
