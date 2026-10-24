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

# Paleta oscura: fondo negro absoluto y acentos/iconos neón.
_DARK_PALETTE = {
    "BG": "#000000",
    "SURFACE": "#050505",
    "SURFACE_ALT": "#0d0d0d",
    "SURFACE_INSET": "#000000",
    "BORDER": "#1a1a1a",
    "BORDER_STRONG": "#333333",
    "TEXT": "#f5f5f5",
    "TEXT_MUTED": "#a3a3a3",
    "TEXT_SECONDARY": "#d4d4d4",
    "TEXT_SUBTLE": "#737373",
    "ON_ACCENT": "#ffffff",
    "APPBAR_BG": "#000000",
    "NAV_BG": "#000000",
    "TABLE_HEAD": "#0d0d0d",
    "INPUT_BG": "#050505",
    "INPUT_BORDER": "#2a2a2a",
    "DISABLED_BG": "#333333",
    "LOGIN_BG": "#000000",
    "LOGIN_CARD": "#050505",
    "LOGIN_INPUT": "#050505",
    "LOGIN_BORDER": "#39ff1444",
    "SHADOW": "#000000aa",
    "PRIMARY": "#0057ff",
    "PRIMARY_DARK": "#003ecc",
    "PRIMARY_SHADOW": "#0057ff55",
    "SUCCESS": "#10b981",
    "SUCCESS_STRONG": "#059669",
    "SUCCESS_TEXT": "#39ff14",
    "SUCCESS_BG": "#00ff9c22",
    "SUCCESS_BG_SOFT": "#00ff9c11",
    "DANGER": "#ef4444",
    "DANGER_TEXT": "#ff5c5c",
    "DANGER_BG": "#ff313122",
    "WARNING": "#ffd60a",
    "AMBER": "#ffb703",
    "WARNING_BG": "#ffd60a22",
    "WARNING_BG_SOFT": "#ffd60a11",
    "INFO": "#00bfff",
    "INFO_TEXT": "#00e5ff",
    "INFO_BG": "#00bfff22",
    "INFO_BG_SOFT": "#00bfff11",
    "INDIGO": "#7c3aed",
    "INDIGO_DARK": "#5b21b6",
    "INDIGO_TEXT": "#c084fc",
    "INDIGO_BG": "#7c3aed22",
    "PURPLE": "#d946ef",
    "PURPLE_TEXT": "#e879f9",
    "PURPLE_BTN": "#7c3aed",
    "PURPLE_BG": "#d946ef22",
    "CYAN": "#00ffff",
    "CYAN_TEXT": "#22d3ee",
    "PINK": "#ff2d95",
    "SKY": "#00bfff",
    "CHIP_BG": "#00ff9c1a",
    "MUTED_BG": "#a3a3a31a",
    # Iconografía neón.
    "ICON_NEON": "#39ff14",
    "ICON_NEON_ALT": "#00ffff",
    "ICON_NEON_PINK": "#ff2d95",
    "ICON_NEON_PURPLE": "#d946ef",
    "ICON_NEON_YELLOW": "#ffd60a",
    "ICON_NEON_ORANGE": "#ff7a00",
    "ICON_NEON_BLUE": "#00bfff",
    "ICON_MUTED": "#4ade80",
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
    # Iconografía: en tema claro se usan tonos accesibles, no neón.
    "ICON_NEON": "#1d4ed8",
    "ICON_NEON_ALT": "#0e7490",
    "ICON_NEON_PINK": "#be185d",
    "ICON_NEON_PURPLE": "#7e22ce",
    "ICON_NEON_YELLOW": "#b45309",
    "ICON_NEON_ORANGE": "#c2410c",
    "ICON_NEON_BLUE": "#1d4ed8",
    "ICON_MUTED": "#64748b",
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

    # Tema claro: se conserva la paleta original.
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        icon_theme=ft.IconTheme(color=ICON_NEON, size=24),
    )

    # Tema oscuro: fondo negro y iconos/acentos neón.
    page.dark_theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=PRIMARY,
            on_primary=ON_ACCENT,
            secondary=ICON_NEON_ALT,
            on_secondary="#000000",
            surface=SURFACE,
            on_surface=TEXT,
            on_surface_variant=ICON_NEON,
            outline=BORDER_STRONG,
            error=DANGER,
            on_error=ON_ACCENT,
        ),
        icon_theme=ft.IconTheme(color=ICON_NEON, size=24),
        appbar_theme=ft.AppBarTheme(bgcolor=APPBAR_BG, color=TEXT),
        navigation_bar_theme=ft.NavigationBarTheme(
            bgcolor=NAV_BG,
            indicator_color=ICON_NEON + "22",
            label_text_style=ft.TextStyle(color=ICON_NEON, size=11),
        ),
        scaffold_bgcolor=BG,
        canvas_color=BG,
        card_bgcolor=SURFACE,
        divider_color=BORDER,
        hint_color=TEXT_SUBTLE,
    )
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
