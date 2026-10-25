"""
Migration: 013_ride_sri_improvements.py
Agrega los datos que faltaban para un RIDE y un XML SRI más completos:

- Dirección del establecimiento y número de agente de retención (empresa).
- Propina e ICE en facturas e ítems de factura.
- Código y tarifa de ICE en productos y servicios.
- ICE en cotizaciones e ítems de cotización (para que al facturarlas se
  conserve el desglose tributario).
"""


def _columnas(cursor, tabla: str) -> set:
    return {row[1] for row in cursor.execute(f"PRAGMA table_info({tabla})").fetchall()}


def _agregar_columnas(cursor, tabla: str, columnas: dict):
    existentes = _columnas(cursor, tabla)
    for columna, definicion in columnas.items():
        if columna not in existentes:
            cursor.execute(
                f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}"
            )


def up(db):
    cursor = db.cursor()

    _agregar_columnas(cursor, "company", {
        "direccion_establecimiento": "TEXT DEFAULT ''",
        "agente_retencion": "TEXT DEFAULT ''",
    })

    _agregar_columnas(cursor, "products", {
        "ice_codigo": "TEXT DEFAULT ''",
        "ice_porcentaje": "REAL DEFAULT 0.0",
    })

    _agregar_columnas(cursor, "services", {
        "ice_codigo": "TEXT DEFAULT ''",
        "ice_porcentaje": "REAL DEFAULT 0.0",
    })

    _agregar_columnas(cursor, "invoices", {
        "ice_total": "REAL DEFAULT 0.0",
        "propina": "REAL DEFAULT 0.0",
    })

    _agregar_columnas(cursor, "invoice_items", {
        "ice_codigo": "TEXT DEFAULT ''",
        "ice_porcentaje": "REAL DEFAULT 0.0",
        "valor_ice": "REAL DEFAULT 0.0",
    })

    _agregar_columnas(cursor, "quotations", {
        "ice_total": "REAL DEFAULT 0.0",
    })

    _agregar_columnas(cursor, "quotation_items", {
        "ice_codigo": "TEXT DEFAULT ''",
        "ice_porcentaje": "REAL DEFAULT 0.0",
        "valor_ice": "REAL DEFAULT 0.0",
    })

    db.commit()


def down(db):
    # SQLite no elimina columnas de forma portable en todas las versiones.
    pass
