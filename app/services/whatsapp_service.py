"""Envío de cotizaciones por WhatsApp mediante enlaces wa.me.

No requiere API ni token: se abre WhatsApp (escritorio o móvil) con el
mensaje preparado. El PDF se comparte como archivo adjunto de forma manual
desde la propia aplicación de WhatsApp.
"""
from urllib.parse import quote


def normalize_phone(phone: str, default_country: str = "593") -> str:
    """Normaliza un teléfono al formato internacional requerido por wa.me.

    Ecuador = 593. Se eliminan espacios, guiones y el '+' inicial. Si el
    número es local (09xxxxxxxx) se agrega el código de país.
    """
    if not phone:
        return ""
    digits = "".join(ch for ch in str(phone) if ch.isdigit())
    if not digits:
        return ""

    if digits.startswith("00"):
        digits = digits[2:]

    # Número local ecuatoriano: se quita el 0 inicial y se agrega 593.
    if digits.startswith("0") and len(digits) >= 9 and not digits.startswith(default_country):
        digits = default_country + digits[1:]
    elif len(digits) == 9 and not digits.startswith(default_country):
        digits = default_country + digits
    elif not digits.startswith(default_country) and len(digits) <= 10:
        digits = default_country + digits.lstrip("0")

    return digits


def build_whatsapp_link(phone: str, message: str) -> str:
    """Construye el enlace wa.me con el mensaje codificado."""
    number = normalize_phone(phone)
    text = quote(message or "")
    if number:
        return f"https://wa.me/{number}?text={text}"
    return f"https://wa.me/?text={text}"


def build_quote_message(quote: dict, items=None, empresa: str = "Nuestra empresa") -> str:
    """Mensaje de texto con el resumen de una cotización (formato WhatsApp)."""
    lines = [
        f"*COTIZACIÓN {quote.get('secuencial', '')}*",
        f"*{empresa}*",
        "",
        f"Cliente: {quote.get('client_nombre', '')}",
        f"Fecha: {quote.get('fecha_emision', '')}",
        f"Válida hasta: {quote.get('fecha_validez', '')}",
        "",
    ]

    for item in (items or []):
        lines.append(
            f"• {item.get('cantidad', 0)} x {item.get('descripcion', '')} "
            f"= ${float(item.get('total') or 0):.2f}"
        )

    lines += [
        "",
        f"Subtotal: ${float(quote.get('subtotal_sin_impuestos') or 0):.2f}",
        f"IVA: ${float(quote.get('iva_total') or 0):.2f}",
        f"*TOTAL: ${float(quote.get('importe_total') or 0):.2f}*",
        "",
        "Adjuntamos el PDF con el detalle. ¡Gracias por su preferencia!",
    ]
    return "\n".join(lines)
