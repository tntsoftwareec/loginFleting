
import flet as ft
from app.views.layouts.main_layout import MainLayout
from app.controllers.help_controller import HelpController
from flet import UrlLauncher

class HelpView:
    def __init__(self, page, router):
        self.page = page
        self.router = router
        self.controller = HelpController()
        self.url_launcher = UrlLauncher()
    
    async def open_docs(self, e):
        await self.url_launcher.launch_url("https://github.com/alexyucra/Fleting")

    async def open_issues(self, e):
        await self.url_launcher.launch_url("https://github.com/alexyucra/fleting/issues")

    async def open_support(self, e):
        await self.url_launcher.launch_url("https://alexyucra.github.io/#contato")

    def render(self):
        

        content = ft.Column(
            spacing=24,
            controls=[
                ft.Text(
                    self.controller.get_title(),
                    size=28,
                    weight=ft.FontWeight.BOLD,
                ),

                ft.Text(
                    "Precisa de ajuda com o Fleting?",
                    size=18,
                    weight=ft.FontWeight.W_500,
                ),

                ft.Text(
                    "Aqui você encontra links úteis para documentação, "
                    "suporte e contribuição com o projeto.",
                    color=ft.Colors.GREY_600,
                ),

                ft.Divider(),

                ft.Button(
                    "📘 Documentação Oficial",
                    icon=ft.Icons.MENU_BOOK,
                    on_click=self.open_docs,
                ),

                ft.Button(
                    "🐛 Reportar um problema",
                    icon=ft.Icons.BUG_REPORT,
                    on_click=self.open_issues,
                ),

                ft.Button(
                    "💬 Precisa de uma automação ou Sistema?",
                    icon=ft.Icons.BUG_REPORT,
                    on_click=self.open_support,
                ),
            ],
        )

        return MainLayout(
            page=self.page,
            content=content,
            router=self.router,
        )
