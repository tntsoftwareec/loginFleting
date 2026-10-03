
import flet as ft
from app.controllers.login_controller import LoginController
from core.state import AppState


def _all_border(width: int, color: str) -> ft.Border:
    """Helper para crear borde uniforme en todos los lados."""
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)


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
            bgcolor="#000000",
            border_color="#334155",
            focused_border_color="#6366f1",
            color="#f8fafc",
            label_style=ft.TextStyle(color="#94a3b8"),
            border_radius=12,
            height=56,
        )

        pass_in = ft.TextField(
            label="Contraseña",
            prefix_icon=ft.Icons.LOCK_OUTLINED,
            password=True,
            can_reveal_password=True,
            bgcolor="#000000",
            border_color="#334155",
            focused_border_color="#6366f1",
            color="#f8fafc",
            label_style=ft.TextStyle(color="#94a3b8"),
            border_radius=12,
            height=56,
        )

        error_text = ft.Text(
            "",
            color="#ef4444",
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
                    ft.Icon(ft.Icons.LOGIN_ROUNDED, color="#ffffff", size=20),
                    ft.Text(
                        "Iniciar Sesión",
                        color="#ffffff",
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
                colors=["#6366f1", "#4f46e5"],
                begin=ft.Alignment(-1, 0),
                end=ft.Alignment(1, 0),
            ),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color="#3b3acc55",
                offset=ft.Offset(0, 8),
            ),
            on_click=do_login,
            ink=True,
        )

        # ── botones rápidos de demo ──────────────────────────────────────────
        def quick_login(demo_email, demo_pass):
            email_in.value = demo_email
            pass_in.value = demo_pass
            self.page.update()
            do_login()

        demo_admin_btn = ft.TextButton(
            "Admin Demo",
            icon=ft.Icons.ADMIN_PANEL_SETTINGS_ROUNDED,
            style=ft.ButtonStyle(color="#6366f1"),
            on_click=lambda e: quick_login("admin@pos.com", "admin123"),
        )

        demo_cajero_btn = ft.TextButton(
            "Cajero Demo",
            icon=ft.Icons.POINT_OF_SALE_ROUNDED,
            style=ft.ButtonStyle(color="#10b981"),
            on_click=lambda e: quick_login("cajero@pos.com", "cajero123"),
        )

        # ── icono de logo ────────────────────────────────────────────────────
        logo_icon = ft.Container(
            content=ft.Image(src="assets/icon.png", width=600, height=600),
            width=100,
            height=100,
            border_radius=50,
            gradient=ft.LinearGradient(
                colors=["#6366f1", "#4f46e5"],
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
            ),
            alignment=ft.Alignment(0, 0),
        )

        # ── tarjeta central ─────────────────────────────────────────────────
        card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Column(
                        controls=[
                            logo_icon,
                            ft.Text(
                                "Bienvenido",
                                color="#f8fafc",
                                size=26,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "Ingresa tus credenciales para continuar",
                                color="#64748b",
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
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Divider(color="#1e293b"),
                                ft.Text(
                                    "Accesos rápidos de prueba:",
                                    color="#475569",
                                    size=11,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Row(
                                    controls=[demo_admin_btn, demo_cajero_btn],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4,
                        ),
                    ),
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=40,
            width=420,
            bgcolor="#000000",
            border_radius=24,
            border=_all_border(1, "#1e293b"),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=60,
                color="#00000066",
                offset=ft.Offset(0, 20),
            ),
        )

        # ── fondo con degradado ─────────────────────────────────────────────
        bg = ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                colors=["#000000", "#0f172a", "#1e1b4b"],
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
