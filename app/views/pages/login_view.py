
import os

import flet as ft
from core import theme as T
from core.paths import ASSETS_DIR
from core.state import AppState
from configs.app_config import AppConfig
from app.controllers.company_controller import CompanyController
from app.controllers.login_controller import LoginController


def _all_border(width: int, color: str) -> ft.Border:
    """Helper para crear borde uniforme en todos los lados."""
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)


def _login_logo_src() -> str:
    """Logo de la empresa configurado en Mi Empresa, o el predeterminado."""
    try:
        company = CompanyController.get_info() or {}
        logo_path = str(company.get("logo_path") or "").strip()
        if logo_path and os.path.isfile(logo_path):
            return logo_path
    except Exception:  # noqa: BLE001
        # Un logo ausente o una BD no inicializada no deben impedir el login.
        pass
    return str(ASSETS_DIR / "image.png")


class LoginView:
    def __init__(self, page: ft.Page, router):
        self.page = page
        self.router = router

    def render(self):
        # ── campos ──────────────────────────────────────────────────────────
        email_in = ft.TextField(
            label="Correo Electrónico",
            hint_text="usuario@ejemplo.com",
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
            keyboard_type=ft.KeyboardType.EMAIL,
            bgcolor=T.LOGIN_INPUT,
            border_color=T.INPUT_BORDER,
            focused_border_color=T.INDIGO,
            color=T.TEXT,
            label_style=ft.TextStyle(color=T.TEXT_MUTED),
            border_radius=12,
            height=56,
        )

        pass_in = ft.TextField(
            label="Contraseña",
            prefix_icon=ft.Icons.LOCK_OUTLINED,
            password=True,
            can_reveal_password=True,
            bgcolor=T.LOGIN_INPUT,
            border_color=T.INPUT_BORDER,
            focused_border_color=T.INDIGO,
            color=T.TEXT,
            label_style=ft.TextStyle(color=T.TEXT_MUTED),
            border_radius=12,
            height=56,
        )

        error_text = ft.Text(
            "",
            color=T.DANGER,
            size=13,
            visible=False,
        )

        # ── lógica de login ──────────────────────────────────────────────────
        def do_login(e=None):
            error_text.visible = False
            email = email_in.value.strip()
            password = pass_in.value

            if not email or not password:
                error_text.value = "Por favor completa todos los campos."
                error_text.visible = True
                self.page.update()
                return

            user = LoginController.authenticate(email, password)
            if user:
                AppState.current_user = user
                self.router.navigate("/")
            else:
                error_text.value = "Correo o contraseña incorrectos."
                error_text.visible = True
                self.page.update()

        email_in.on_submit = lambda e: do_login()
        pass_in.on_submit = lambda e: do_login()

        # ── botón principal ─────────────────────────────────────────────────
        login_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.LOGIN_ROUNDED, color=T.ICON_NEON, size=20),
                    ft.Text(
                        "Iniciar Sesión",
                        color=T.ON_ACCENT,
                        size=16,
                        weight=ft.FontWeight.W_600,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            padding=16,
            border_radius=12,
            gradient=ft.LinearGradient(
                colors=[T.INDIGO, T.INDIGO_DARK],
                begin=ft.Alignment(-1, 0),
                end=ft.Alignment(1, 0),
            ),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=T.PRIMARY_SHADOW,
                offset=ft.Offset(0, 8),
            ),
            on_click=do_login,
            ink=True,
        )

        # ── logo de la empresa ──────────────────────────────────────────────
        logo_icon = ft.Container(
            content=ft.Image(
                src=_login_logo_src(),
                width=96,
                height=96,
                fit=ft.BoxFit.CONTAIN,
            ),
            width=112,
            height=112,
            padding=8,
            border_radius=20,
            bgcolor=T.LOGIN_INPUT,
            border=_all_border(1, T.LOGIN_BORDER),
            alignment=ft.Alignment(0, 0),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

        # ── tarjeta central ─────────────────────────────────────────────────
        card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Column(
                        controls=[
                            logo_icon,
                            ft.Text(
                                AppConfig.APP_NAME,
                                color=T.TEXT,
                                size=28,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "Bienvenido. Ingresa tus credenciales para continuar",
                                color=T.TEXT_SUBTLE,
                                size=13,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    ft.Container(height=8),
                    email_in,
                    pass_in,
                    error_text,
                    ft.Container(height=4),
                    login_btn,
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=20,
            width=min(420, self.page.width - 40) if self.page.width > 0 else 420,
            bgcolor=T.LOGIN_CARD,
            border_radius=24,
            border=_all_border(1, T.LOGIN_BORDER),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=60,
                color=T.SHADOW,
                offset=ft.Offset(0, 20),
            ),
        )

        # ── fondo con degradado ─────────────────────────────────────────────
        bg = ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                colors=[T.LOGIN_BG],
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
            ),
            content=ft.Container(
                content=card,
                alignment=ft.Alignment(0, 0),
                expand=True,
            ),
        )

        # IMPORTANTE: el router hace page.add(control), NO page.views.append(ft.View)
        # Por eso retornamos el control directamente (igual que MainLayout en otras vistas).
        return ft.Column(controls=[bg], expand=True)
