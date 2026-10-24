"""
Migration: 008_product_images.py
Añade la ruta de la imagen del producto (idempotente).
"""


def up(db):
    cursor = db.cursor()
    columns = {row[1] for row in cursor.execute("PRAGMA table_info(products)").fetchall()}

    if "imagen_path" not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN imagen_path TEXT DEFAULT ''")
        db.commit()


def down(db):
    # SQLite no soporta DROP COLUMN de forma portable en todas las versiones.
    pass
