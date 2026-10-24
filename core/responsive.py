
MOBILE_BREAKPOINT = 800


def get_device_type(width):
    if width is None:
        return "desktop"
    if width <= 600:
        return "mobile"
    elif width <= 1024:
        return "tablet"
    return "desktop"


def is_mobile(width) -> bool:
    """True cuando la interfaz debe usar el layout compacto (móvil)."""
    return width is not None and width < MOBILE_BREAKPOINT


def get_dialog_width(page, preferred: int = 420) -> int:
    """Ancho del contenido de un diálogo, ajustado a móvil."""
    width = getattr(page, "width", None) or 1280
    if not is_mobile(width):
        return preferred
    return int(max(240, width - 72))
