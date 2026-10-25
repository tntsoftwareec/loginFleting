"""Catálogos y utilidades de códigos del SRI Ecuador.

Centraliza los códigos que se comparten entre el XML, el RIDE y las vistas
para evitar que cada pantalla mantenga su propia lista de formas de pago.
"""

import unicodedata

# forma_pago interna -> (código SRI, etiqueta legible)
FORMAS_PAGO_SRI = {
    "EFECTIVO": ("01", "Efectivo / Sin utilización del sistema financiero"),
    "TARJETA_CREDITO": ("19", "Tarjeta de crédito"),
    "TARJETA_DEBITO": ("16", "Tarjeta de débito"),
    "TRANSFERENCIA": ("20", "Transferencia bancaria / Otros con utilización del sistema financiero"),
    # Compatibilidad con facturas/cotizaciones antiguas que guardaban "TARJETA".
    "TARJETA": ("20", "Tarjeta (sin especificar)"),
    "OTROS": ("20", "Otros con utilización del sistema financiero"),
}

# Opciones que se muestran en el POS y en la facturación de cotizaciones.
FORMAS_PAGO_OPCIONES = [
    ("EFECTIVO", "Efectivo / Sin sistema financiero"),
    ("TARJETA_CREDITO", "Tarjeta de crédito"),
    ("TARJETA_DEBITO", "Tarjeta de débito"),
    ("TRANSFERENCIA", "Transferencia bancaria"),
]

_ALIASES = {
    "EFECTIVO": "EFECTIVO",
    "CONTADO": "EFECTIVO",
    "TARJETA": "TARJETA",
    "TARJETA_CREDITO": "TARJETA_CREDITO",
    "TARJETA_DE_CREDITO": "TARJETA_CREDITO",
    "CREDITO": "TARJETA_CREDITO",
    "TARJETA_DEBITO": "TARJETA_DEBITO",
    "TARJETA_DE_DEBITO": "TARJETA_DEBITO",
    "DEBITO": "TARJETA_DEBITO",
    "TRANSFERENCIA": "TRANSFERENCIA",
    "TRANSFERENCIA_BANCARIA": "TRANSFERENCIA",
    "DEPOSITO": "TRANSFERENCIA",
    "OTROS": "OTROS",
}


def normalizar_forma_pago(forma_pago: str) -> str:
    """Devuelve la clave interna normalizada de una forma de pago."""
    valor = str(forma_pago or "").strip().upper()
    valor = "".join(
        char for char in unicodedata.normalize("NFKD", valor)
        if not unicodedata.combining(char)
    )
    valor = valor.replace("-", "_").replace(" ", "_")
    return _ALIASES.get(valor, valor)


def codigo_forma_pago(forma_pago: str) -> str:
    """Código de forma de pago del SRI (01, 16, 19 o 20)."""
    clave = normalizar_forma_pago(forma_pago)
    return FORMAS_PAGO_SRI.get(clave, FORMAS_PAGO_SRI["OTROS"])[0]


def etiqueta_forma_pago(forma_pago: str) -> str:
    """Etiqueta legible para el RIDE o la interfaz."""
    clave = normalizar_forma_pago(forma_pago)
    if clave in FORMAS_PAGO_SRI:
        return FORMAS_PAGO_SRI[clave][1]
    return str(forma_pago or "").strip() or "Otros"


def es_forma_pago_valida(forma_pago: str) -> bool:
    """Indica si la forma de pago pertenece al catálogo conocido."""
    return normalizar_forma_pago(forma_pago) in FORMAS_PAGO_SRI


def validar_ice(codigo: str, porcentaje) -> tuple:
    """Valida el código y la tarifa de ICE de un producto, servicio o ítem.

    Returns:
        ``(ok, (codigo_normalizado, tarifa) | mensaje_error)``.
    """
    codigo = str(codigo or "").strip()
    try:
        tarifa = float(porcentaje or 0)
    except (TypeError, ValueError):
        return False, "La tarifa de ICE debe ser un valor numérico."
    if tarifa < 0:
        return False, "La tarifa de ICE no puede ser negativa."
    if tarifa > 0:
        if not (codigo.isdigit() and len(codigo) == 4):
            return False, (
                "Si el ítem aplica ICE, el código del SRI debe tener 4 dígitos "
                "(ej. 3031)."
            )
    else:
        codigo = ""
    return True, (codigo, tarifa)


def calcular_totales_linea(
    cantidad,
    precio_unitario,
    descuento=0.0,
    iva_porcentaje=0.0,
    ice_codigo: str = "",
    ice_porcentaje=0.0,
) -> dict:
    """Calcula los valores tributarios de una línea de factura/cotización.

    La base del IVA incluye el ICE, conforme a la definición del SRI: la base
    está formada por el precio de venta más los impuestos que se carguen en la
    factura. El ICE no forma parte de ``subtotal`` (precioTotalSinImpuesto),
    pero sí de la base sobre la que se calcula el IVA.
    """
    ok, ice_value = validar_ice(ice_codigo, ice_porcentaje)
    if not ok:
        raise ValueError(ice_value)
    ice_codigo_val, ice_p = ice_value

    try:
        cantidad_flt = float(cantidad)
        precio_flt = float(precio_unitario)
        descuento_flt = float(descuento or 0)
        iva_p = float(iva_porcentaje or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError("Valores numéricos de cantidad, precio, descuento o IVA inválidos.") from exc

    subtotal = max(0.0, (cantidad_flt * precio_flt) - descuento_flt)
    valor_ice = (subtotal * (ice_p / 100.0)) if ice_p > 0 else 0.0
    base_iva = subtotal + valor_ice
    valor_iva = (base_iva * (iva_p / 100.0)) if iva_p > 0 else 0.0

    return {
        "subtotal": subtotal,
        "iva_porcentaje": iva_p,
        "valor_iva": valor_iva,
        "ice_codigo": ice_codigo_val,
        "ice_porcentaje": ice_p,
        "valor_ice": valor_ice,
        "total": subtotal + valor_ice + valor_iva,
    }

