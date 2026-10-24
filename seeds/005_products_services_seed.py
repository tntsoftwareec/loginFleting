"""
Seed: 005_products_services_seed.py
Seeds initial products and services records.
"""

def run(db):
    cursor = db.cursor()

    default_products = [
        ("PROD-001", "Laptop HP ProBook 440 G8", "Intel Core i5 11va Gen, 16GB RAM, 512GB SSD", 850.00, 680.00, 15, 15.0, "Tecnología"),
        ("PROD-002", "Monitor LG 27 pulgadas Full HD", "Panel IPS, 75Hz, HDMI, DisplayPort", 220.00, 165.00, 25, 15.0, "Tecnología"),
        ("PROD-003", "Teclado Mecánico Inalámbrico RGB", "Switches Red, Conexión Bluetooth / USB-C", 65.00, 42.00, 40, 15.0, "Accesorios"),
        ("PROD-004", "Mouse Óptico Inalámbrico Ergológico", "Sensor 4000 DPI, recargable", 28.50, 16.00, 50, 15.0, "Accesorios"),
        ("PROD-005", "Impresora Multifuncional Epson EcoTank", "Impresión continua a color con Wi-Fi", 240.00, 190.00, 10, 15.0, "Oficina"),
        ("PROD-006", "Paquete Papel Bond A4 75g (Resma)", "Resma de 500 hojas blancas", 4.50, 3.20, 100, 15.0, "Suministros"),
    ]

    for cod, nom, desc, pre, cos, st, iva, cat in default_products:
        cursor.execute(
            """
            INSERT OR IGNORE INTO products (codigo, nombre, descripcion, precio, costo, stock, iva_porcentaje, categoria, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """,
            (cod, nom, desc, pre, cos, st, iva, cat)
        )
        # En una instalación nueva las migraciones corren antes que los seeds,
        # por lo que el movimiento inicial de estos productos se crea aquí.
        cursor.execute("SELECT id FROM products WHERE codigo = ?", (cod,))
        product_row = cursor.fetchone()
        if product_row and st > 0:
            cursor.execute(
                "SELECT COUNT(*) FROM inventory_movements "
                "WHERE product_id = ? AND tipo = 'INICIAL'",
                (product_row[0],),
            )
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    """
                    INSERT INTO inventory_movements (
                        product_id, product_codigo, product_nombre, tipo,
                        cantidad, stock_anterior, stock_nuevo, motivo, referencia
                    ) VALUES (?, ?, ?, 'INICIAL', ?, 0, ?, ?, ?)
                    """,
                    (
                        product_row[0],
                        cod,
                        nom,
                        st,
                        st,
                        "Stock inicial del producto",
                        "Seed de productos",
                    ),
                )

    default_services = [
        ("SERV-001", "Mantenimiento Preventivo de Equipos", "Limpieza física, cambio de pasta térmica y revisión de hardware", 35.00, 15.0, "Mantenimiento"),
        ("SERV-002", "Instalación y Configuración de Software", "Instalación de S.O., antivirus y suites de oficina", 25.00, 15.0, "Soporte Técnico"),
        ("SERV-003", "Asesoría y Consultoría Informática (Hora)", "Diagnóstico de red, seguridad e infraestructura IT", 50.00, 15.0, "Consultoría"),
        ("SERV-004", "Desarrollo de Software a Medida (Hora)", "Programación y personalización de módulos web/desktop", 60.00, 15.0, "Desarrollo"),
        ("SERV-005", "Capacitación de Personal (Sesión 2h)", "Capacitación en uso de sistemas informáticos y POS", 100.00, 0.0, "Capacitación")
    ]

    for cod, nom, desc, pre, iva, cat in default_services:
        cursor.execute(
            """
            INSERT OR IGNORE INTO services (codigo, nombre, descripcion, precio, iva_porcentaje, categoria, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
            """,
            (cod, nom, desc, pre, iva, cat)
        )

    db.commit()
