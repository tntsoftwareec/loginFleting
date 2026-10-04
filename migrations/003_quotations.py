"""
Migration: 003_quotations.py
Creates tables for quotations (cotizaciones) and quotation_items.
"""

def up(db):
    cursor = db.cursor()

    # Table: quotations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quotations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            secuencial TEXT NOT NULL UNIQUE,
            client_id INTEGER,
            client_nombre TEXT NOT NULL,
            client_identificacion TEXT NOT NULL,
            client_email TEXT NOT NULL,
            client_direccion TEXT,
            fecha_emision TEXT NOT NULL,
            fecha_validez TEXT NOT NULL,
            subtotal_15 REAL DEFAULT 0.0,
            subtotal_0 REAL DEFAULT 0.0,
            subtotal_sin_impuestos REAL DEFAULT 0.0,
            total_descuento REAL DEFAULT 0.0,
            iva_total REAL DEFAULT 0.0,
            importe_total REAL DEFAULT 0.0,
            estado TEXT DEFAULT 'EMITIDA',
            pdf_path TEXT,
            notas TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL
        )
    ''')

    # Table: quotation_items
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quotation_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quotation_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            item_id INTEGER,
            codigo TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            cantidad REAL NOT NULL DEFAULT 1,
            precio_unitario REAL NOT NULL DEFAULT 0.0,
            descuento REAL DEFAULT 0.0,
            subtotal REAL NOT NULL DEFAULT 0.0,
            iva_porcentaje REAL DEFAULT 15.0,
            valor_iva REAL DEFAULT 0.0,
            total REAL NOT NULL DEFAULT 0.0,
            FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE
        )
    ''')

    db.commit()

def down(db):
    cursor = db.cursor()
    cursor.execute('DROP TABLE IF EXISTS quotation_items')
    cursor.execute('DROP TABLE IF EXISTS quotations')
    db.commit()
