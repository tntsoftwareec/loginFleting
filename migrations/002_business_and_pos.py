"""
Migration: 002_business_and_pos.py
Creates tables for clients, suppliers, products, services, company, invoices, and invoice_items.
"""

def up(db):
    cursor = db.cursor()

    # Table: clients
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_documento TEXT DEFAULT 'CEDULA',
            identificacion TEXT NOT NULL UNIQUE,
            razon_social TEXT NOT NULL,
            email TEXT NOT NULL,
            telefono TEXT,
            direccion TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table: suppliers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_documento TEXT DEFAULT 'RUC',
            identificacion TEXT NOT NULL UNIQUE,
            razon_social TEXT NOT NULL,
            email TEXT NOT NULL,
            telefono TEXT,
            direccion TEXT,
            contacto TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table: products
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            precio REAL NOT NULL DEFAULT 0.0,
            costo REAL DEFAULT 0.0,
            stock INTEGER DEFAULT 0,
            iva_porcentaje REAL DEFAULT 15.0,
            categoria TEXT DEFAULT 'General',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table: services
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            precio REAL NOT NULL DEFAULT 0.0,
            iva_porcentaje REAL DEFAULT 15.0,
            categoria TEXT DEFAULT 'Servicios',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table: company
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS company (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ruc TEXT NOT NULL DEFAULT '1790000000001',
            razon_social TEXT NOT NULL DEFAULT 'MI EMPRESA S.A.',
            nombre_comercial TEXT DEFAULT 'MI NEGOCIO',
            direccion_matriz TEXT DEFAULT 'Av. Principal 123',
            telefono TEXT DEFAULT '0999999999',
            email TEXT DEFAULT 'facturacion@empresa.com',
            ambiente_sri INTEGER DEFAULT 1,
            establecimiento TEXT DEFAULT '001',
            punto_emision TEXT DEFAULT '001',
            secuencial_factura INTEGER DEFAULT 1,
            contribuyente_especial TEXT DEFAULT '',
            obligado_contabilidad TEXT DEFAULT 'NO',
            firma_path TEXT DEFAULT '',
            firma_pass TEXT DEFAULT '',
            sri_email TEXT DEFAULT 'recepcion.sri@sri.gob.ec',
            smtp_host TEXT DEFAULT 'smtp.gmail.com',
            smtp_port INTEGER DEFAULT 587,
            smtp_user TEXT DEFAULT '',
            smtp_pass TEXT DEFAULT '',
            smtp_ssl INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table: invoices
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            secuencial TEXT NOT NULL UNIQUE,
            clave_acceso TEXT UNIQUE,
            client_id INTEGER,
            client_nombre TEXT NOT NULL,
            client_identificacion TEXT NOT NULL,
            client_email TEXT NOT NULL,
            client_direccion TEXT,
            fecha_emision TEXT NOT NULL,
            subtotal_15 REAL DEFAULT 0.0,
            subtotal_0 REAL DEFAULT 0.0,
            subtotal_sin_impuestos REAL DEFAULT 0.0,
            total_descuento REAL DEFAULT 0.0,
            iva_total REAL DEFAULT 0.0,
            importe_total REAL DEFAULT 0.0,
            forma_pago TEXT DEFAULT 'EFECTIVO',
            estado TEXT DEFAULT 'GENERADA',
            xml_path TEXT,
            pdf_path TEXT,
            sri_mensaje TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL
        )
    ''')

    # Table: invoice_items
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
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
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
        )
    ''')

    db.commit()

def down(db):
    cursor = db.cursor()
    cursor.execute('DROP TABLE IF EXISTS invoice_items')
    cursor.execute('DROP TABLE IF EXISTS invoices')
    cursor.execute('DROP TABLE IF EXISTS company')
    cursor.execute('DROP TABLE IF EXISTS services')
    cursor.execute('DROP TABLE IF EXISTS products')
    cursor.execute('DROP TABLE IF EXISTS suppliers')
    cursor.execute('DROP TABLE IF EXISTS clients')
    db.commit()
