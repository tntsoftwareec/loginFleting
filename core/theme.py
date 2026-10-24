"""Paleta adaptativa de la interfaz (modo claro / oscuro).

Las vistas usan tokens semánticos (``T.TEXT``, ``T.SURFACE``, ``T.BORDER``…)
en lugar de colores fijos. Al cambiar de tema se actualizan los valores del
módulo y se vuelve a renderizar la vista, de modo que todos los controles
toman la paleta correcta.

Uso:
    from core import theme as T

    ft.Text("Hola", color=T.TEXT)
    ft.Container(bgcolor=T.SURFACE, border=T.border())

    theme.apply(page, "light")   # aplica tema y fondo de página
"""
from __future__ import annotations

import flet as ft

# Modos que puede elegir el usuario.
LIGHT = "light"
DARK = "dark"
SYSTEM = "system"

_CHOICES = (LIGHT, DARK, SYSTEM)

# Paleta oscura (diseño original de la aplicación).
_DARK_PALETTE = {
    "BG": "#0f172a",
    "SURFACE": "#0f172a",
    "SURFACE_ALT": "#1e293b",
    "SURFACE_INSET": "#0b1220",
    "BORDER": "#1e293b",
    "BORDER_STRONG": "#334155",
    "TEXT": "#f8fafc",
    "TEXT_MUTED": "#94a3b8",
    "TEXT_SECONDARY": "#cbd5e1",
    "TEXT_SUBTLE": "#64748b",
    "ON_ACCENT": "#ffffff",
    "APPBAR_BG": "#0f172a",
    "NAV_BG": "#0f172a",
    "TABLE_HEAD": "#1e293b",
    "INPUT_BG": "#0f172a",
    "INPUT_BORDER": "#334155",
    "DISABLED_BG": "#475569",
    "LOGIN_BG": "#000000",
    "LOGIN_CARD": "#000000",
    "LOGIN_INPUT": "#000000",
    "LOGIN_BORDER": "#1E3B36",
    "SHADOW": "#00000066",
    "PRIMARY": "#2563eb",
    "PRIMARY_DARK": "#1d4ed8",
    "PRIMARY_SHADOW": "#3b3acc55",
    "SUCCESS": "#10b981",
    "SUCCESS_STRONG": "#059669",
    "SUCCESS_TEXT": "#34d399",
    "SUCCESS_BG": "#065f4633",
    "SUCCESS_BG_SOFT": "#065f4622",
    "DANGER": "#ef4444",
    "DANGER_TEXT": "#f87171",
    "DANGER_BG": "#991b1b33",
    "WARNING": "#fbbf24",
    "AMBER": "#f59e0b",
    "WARNING_BG": "#78350f33",
    "WARNING_BG_SOFT": "#78350f22",
    "INFO": "#3b82f6",
    "INFO_TEXT": "#60a5fa",
    "INFO_BG": "#1e40af33",
    "INFO_BG_SOFT": "#0284c722",
    "INDIGO": "#6366f1",
    "INDIGO_DARK": "#4f46e5",
    "INDIGO_TEXT": "#818cf8",
    "INDIGO_BG": "#1e1b4b",
    "PURPLE": "#a855f7",
    "PURPLE_TEXT": "#a78bfa",
    "PURPLE_BTN": "#7c3aed",
    "PURPLE_BG": "#3730a322",
    "CYAN": "#06b6d4",
    "CYAN_TEXT": "#38bdf8",
    "PINK": "#ec4899",
    "SKY": "#0284c7",
    "CHIP_BG": "#064e3b",
    "MUTED_BG": "#64748b15",
    # Colores de marca (no cambian entre temas).
    "WHATSAPP": "#25d366",
    "LOGO_START": "#8CA326",
    "LOGO_END": "#55FD07",
}

# Paleta clara: mismos tokens con contrastes pensados para fondos blancos.
_LIGHT_PALETTE = {
    "BG": "#f1f5f9",
    "SURFACE": "#ffffff",
    "SURFACE_ALT": "#e2e8f0",
    "SURFACE_INSET": "#f8fafc",
    "BORDER": "#cbd5e1",
    "BORDER_STRONG": "#94a3b8",
    "TEXT": "#0f172a",
    "TEXT_MUTED": "#475569",
    "TEXT_SECONDARY": "#334155",
    "TEXT_SUBTLE": "#64748b",
    "ON_ACCENT": "#ffffff",
    "APPBAR_BG": "#ffffff",
    "NAV_BG": "#ffffff",
    "TABLE_HEAD": "#e2e8f0",
    "INPUT_BG": "#ffffff",
    "INPUT_BORDER": "#94a3b8",
    "DISABLED_BG": "#64748b",
    "LOGIN_BG": "#f1f5f9",
    "LOGIN_CARD": "#ffffff",
    "LOGIN_INPUT": "#ffffff",
    "LOGIN_BORDER": "#cbd5e1",
    "SHADOW": "#0f172a22",
    "PRIMARY": "#1d4ed8",
    "PRIMARY_DARK": "#1e40af",
    "PRIMARY_SHADOW": "#1d4ed833",
    "SUCCESS": "#047857",
    "SUCCESS_STRONG": "#047857",
    "SUCCESS_TEXT": "#047857",
    "SUCCESS_BG": "#d1fae5",
    "SUCCESS_BG_SOFT": "#ecfdf5",
    "DANGER": "#dc2626",
    "DANGER_TEXT": "#b91c1c",
    "DANGER_BG": "#fee2e2",
    "WARNING": "#b45309",
    "AMBER": "#b45309",
    "WARNING_BG": "#fef3c7",
    "WARNING_BG_SOFT": "#fffbeb",
    "INFO": "#1d4ed8",
    "INFO_TEXT": "#1d4ed8",
    "INFO_BG": "#dbeafe",
    "INFO_BG_SOFT": "#e0f2fe",
    "INDIGO": "#4338ca",
    "INDIGO_DARK": "#3730a3",
    "INDIGO_TEXT": "#4338ca",
    "INDIGO_BG": "#e0e7ff",
    "PURPLE": "#7e22ce",
    "PURPLE_TEXT": "#6d28d9",
    "PURPLE_BTN": "#6d28d9",
    "PURPLE_BG": "#ede9fe",
    "CYAN": "#0e7490",
    "CYAN_TEXT": "#0369a1",
    "PINK": "#be185d",
    "SKY": "#0369a1",
    "CHIP_BG": "#d1fae5",
    "MUTED_BG": "#e2e8f0",
    # Colores de marca (no cambian entre temas).
    "WHATSAPP": "#25d366",
    "LOGO_START": "#8CA326",
    "LOGO_END": "#55FD07",
}

# Estado del módulo: elección del usuario y modo realmente aplicado.
_choice = SYSTEM
_mode = DARK


def _install(palette: dict) -> None:
    globals().update(palette)


def resolve(choice: str, platform_brightness=None) -> str:
    """Devuelve ``"light"`` o ``"dark"`` para una elección del usuario."""
    if choice == LIGHT:
        return LIGHT
    if choice == DARK:
        return DARK
    # SYSTEM: seguimos el brillo notificado por la plataforma.
    if platform_brightness == ft.Brightness.DARK:
        return DARK
    return LIGHT


def set_mode(choice: str, platform_brightness=None) -> str:
    """Activa la paleta correspondiente y devuelve el modo resuelto."""
    global _choice, _mode

    _choice = choice if choice in _CHOICES else SYSTEM
    _mode = resolve(_choice, platform_brightness)
    _install(_LIGHT_PALETTE if _mode == LIGHT else _DARK_PALETTE)
    return _mode


def current_mode() -> str:
    return _mode


def current_choice() -> str:
    return _choice


def is_dark() -> bool:
    return _mode == DARK


def apply(page: ft.Page, choice: str | None = None) -> str:
    """Aplica el tema a la página (colores de Flet + fondo)."""
    mode = set_mode(choice or _choice, getattr(page, "platform_brightness", None))

    page.theme_mode = ft.ThemeMode.DARK if mode == DARK else ft.ThemeMode.LIGHT
    page.bgcolor = BG
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE)
    page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE)
    return mode


def border(width: int = 1, color: str | None = None) -> ft.Border:
    """Borde uniforme usando la paleta actual."""
    side = ft.BorderSide(width, color or BORDER)
    return ft.Border(top=side, right=side, bottom=side, left=side)


def all_border(width: int = 1, color: str | None = None) -> ft.Border:
    """Alias de :func:`border` para las vistas que usan ``_all_border``."""
    return border(width, color)


# Paleta inicial (oscura) hasta que ``main`` aplique la preferencia guardada.
_install(_DARK_PALETTE)
