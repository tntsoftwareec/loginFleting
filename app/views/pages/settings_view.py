import flet as ft
from core import preferences, theme
from core.state import AppState
from core.i18n import I18n
from app.views.layouts.main_layout import MainLayout
from app.controllers.settings_controller import SettingsController

T = theme


class SettingsView:
    def __init__(self, page, router):
        self.page = page
        self.router = router
        self.controller = SettingsController()

    def _change_language(self, lang: str):
        AppState.language = lang
        preferences.save(language=lang)
        I18n.load(lang)
        # Re-renderiza la vista actual para aplicar los textos del nuevo idioma.
        self.router.rerender()

    def _change_theme(self, mode: str):
        AppState.theme_mode = mode
        preferences.save(theme_mode=mode)
        theme.apply(self.page, mode)
        # Re-renderiza para que todas las vistas reconstruyan sus controles
        # con los colores de la nueva paleta.
        self.router.rerender()

    def render(self):
        content = ft.Column(
            spacing=24,
            controls=[
                ft.Text(
                    self.controller.get_title(),
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=T.TEXT,
                ),

                ft.Container(
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text(
                                I18n.t("settings.theme"),
                                size=16,
                                color=T.TEXT_MUTED,
                            ),
                            ft.RadioGroup(
                                value=AppState.theme_mode,
                                on_change=lambda e: self._change_theme(e.control.value),
                                content=ft.Column(
                                    controls=[
                                        ft.Radio(
                                            value=theme.LIGHT,
                                            label=I18n.t("settings.theme_light"),
                                        ),
                                        ft.Radio(
                                            value=theme.DARK,
                                            label=I18n.t("settings.theme_dark"),
                                        ),
                                        ft.Radio(
                                            value=theme.SYSTEM,
                                            label=I18n.t("settings.theme_system"),
                                        ),
                                    ]
                                ),
                            ),
                        ],
                    ),
                    padding=16,
                    bgcolor=T.SURFACE,
                    border_radius=12,
                    border=T.border(),
                ),

                ft.Container(
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text(
                                I18n.t("settings.language"),
                                size=16,
                                color=T.TEXT_MUTED,
                            ),
                            ft.RadioGroup(
                                value=AppState.language,
                                on_change=lambda e: self._change_language(e.control.value),
                                content=ft.Column(
                                    controls=[
                                        ft.Radio(value="pt", label="Português 🇧🇷"),
                                        ft.Radio(value="en", label="English 🇺🇸"),
                                        ft.Radio(value="es", label="Español 🇪🇸"),
                                    ]
                                ),
                            ),
                        ],
                    ),
                    padding=16,
                    bgcolor=T.SURFACE,
                    border_radius=12,
                    border=T.border(),
                ),
            ],
        )

        return MainLayout(
            page=self.page,
            content=content,
            router=self.router,
        )
