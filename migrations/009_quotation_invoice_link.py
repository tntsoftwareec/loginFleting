"""
Migration: 009_quotation_invoice_link.py
Vincula una cotización con la factura generada a partir de ella.
"""


def up(db):
    cursor = db.cursor()
    columns = {row[1] for row in cursor.execute("PRAGMA table_info(quotations)").fetchall()}

    if "invoice_id" not in columns:
        cursor.execute("ALTER TABLE quotations ADD COLUMN invoice_id INTEGER")
        db.commit()


def down(db):
    # SQLite no soporta DROP COLUMN de forma portable en todas las versiones.
    pass
