"""
Migration: 006_company_secuencial.py
Añade la columna secuencial_cotizacion a la tabla company (idempotente).
"""


def up(db):
    cursor = db.cursor()
    columns = {row[1] for row in cursor.execute("PRAGMA table_info(company)").fetchall()}

    if "secuencial_cotizacion" not in columns:
        cursor.execute("ALTER TABLE company ADD COLUMN secuencial_cotizacion INTEGER DEFAULT 1")
        db.commit()


def down(db):
    # SQLite antiguo no soporta DROP COLUMN de forma portable.
    pass
