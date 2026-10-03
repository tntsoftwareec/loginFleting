
import flet as ft
from app.views.layouts.main_layout import MainLayout

class HomeView:
    def __init__(self, page, router):
        self.page = page
        self.router = router
    
    def render(self):
        content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=24,
            controls=[
                ft.Image(
                    src="icon.png",
                    width=96,
                    height=96,
                    fit="contain",
                ),
                ft.Text(
                    "Fleting Framework",
                    size=36,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Micro Framework MVC for Flet",
                    size=16,
                    color=ft.Colors.GREY_600,
                ),
                ft.Text(
                    "Build modern applications with a clear architecture, "
                    "Dynamic routing and productive CLI.",
                    size=14,
                    text_align=ft.TextAlign.CENTER,
                    width=420,
                ),

                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=16,
                    controls=[
                        ft.FilledButton(
                            "Usuarios",
                            icon=ft.Icons.SUPERVISED_USER_CIRCLE_ROUNDED,
                            style=ft.ButtonStyle(
                                bgcolor="#6366f1",
                                color="#ffffff",
                            ),
                            on_click=lambda e: self.router.navigate("/users"),
                        ),
                        ft.OutlinedButton(
                            "Roles",
                            icon=ft.Icons.ADMIN_PANEL_SETTINGS_ROUNDED,
                            on_click=lambda e: self.router.navigate("/roles"),
                        ),
                        ft.OutlinedButton(
                            "Settings",
                            icon=ft.Icons.SETTINGS,
                            on_click=lambda e: self.router.navigate("/settings"),
                        ),
                    ],
                ),
            ],
        )

        # LAYOUT
        return MainLayout(
            page=self.page,
            content=content,
            router=self.router,
        )
