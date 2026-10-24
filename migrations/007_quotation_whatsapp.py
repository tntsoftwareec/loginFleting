"""
Migration: 007_quotation_whatsapp.py
Añade la columna enviada_whatsapp a la tabla quotations (idempotente).
"""


def up(db):
    cursor = db.cursor()
    columns = {row[1] for row in cursor.execute("PRAGMA table_info(quotations)").fetchall()}

    if "enviada_whatsapp" not in columns:
        cursor.execute("ALTER TABLE quotations ADD COLUMN enviada_whatsapp INTEGER DEFAULT 0")
        db.commit()


def down(db):
    # SQLite antiguo no soporta DROP COLUMN de forma portable.
    pass
