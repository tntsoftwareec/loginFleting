"""
Migration: 010_inventory.py
Crea el historial de movimientos de inventario y agrega el stock mínimo
configurable a los productos.
"""


def up(db):
    cursor = db.cursor()

    product_columns = {
        row[1] for row in cursor.execute("PRAGMA table_info(products)").fetchall()
    }
    if "stock_minimo" not in product_columns:
        cursor.execute(
            "ALTER TABLE products ADD COLUMN stock_minimo INTEGER DEFAULT 5"
        )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            product_codigo TEXT,
            product_nombre TEXT,
            tipo TEXT NOT NULL,
            cantidad INTEGER NOT NULL DEFAULT 0,
            stock_anterior INTEGER NOT NULL DEFAULT 0,
            stock_nuevo INTEGER NOT NULL DEFAULT 0,
            motivo TEXT,
            referencia TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_inventory_movements_product
        ON inventory_movements(product_id, id)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_inventory_movements_created
        ON inventory_movements(created_at)
        """
    )

    # Crea un movimiento inicial para que el historial arranque con el stock
    # que ya tenían los productos al instalar esta versión. Solo se ejecuta
    # una vez y únicamente si la tabla está vacía.
    cursor.execute("SELECT COUNT(*) FROM inventory_movements")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "SELECT id, codigo, nombre, stock FROM products WHERE stock > 0"
        )
        for product_id, codigo, nombre, stock in cursor.fetchall():
            cursor.execute(
                """
                INSERT INTO inventory_movements (
                    product_id, product_codigo, product_nombre, tipo,
                    cantidad, stock_anterior, stock_nuevo, motivo, referencia
                ) VALUES (?, ?, ?, 'INICIAL', ?, 0, ?, ?, ?)
                """,
                (
                    product_id,
                    codigo,
                    nombre,
                    int(stock),
                    int(stock),
                    "Stock inicial del producto",
                    "Migración de inventario",
                ),
            )

    db.commit()


def down(db):
    # SQLite no elimina columnas de forma portable. La tabla de movimientos
    # se conserva para no perder el historial.
    pass
