"""
Migration: 011_company_logo.py
Agrega la ruta del logo personalizado de la empresa.
"""


def up(db):
    cursor = db.cursor()
    columns = {
        row[1] for row in cursor.execute("PRAGMA table_info(company)").fetchall()
    }
    if "logo_path" not in columns:
        cursor.execute(
            "ALTER TABLE company ADD COLUMN logo_path TEXT DEFAULT ''"
        )
    db.commit()


def down(db):
    # SQLite no elimina columnas de forma portable.
    pass
