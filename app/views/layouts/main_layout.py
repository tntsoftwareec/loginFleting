import flet as ft
from core import theme as T
from core.state import AppState
from core.i18n import I18n
from configs.routes import ROUTES
from configs.app_config import AppConfig

class MainLayout(ft.Column):
    def __init__(self, page, content, router):
        super().__init__(expand=True)
        self._page = page
        self.router = router
        self.content = content

        self._build()

    def _build(self):
        self.controls.clear()

        # TOP BAR → chrome nativo de la página (page.appbar), no un control más.
        # El router lo limpia en cada navegación para que rutas sin layout
        # (p. ej. /login) no hereden la barra de una vista anterior.
        self._page.appbar = self._top_bar()

        # CONTENT
        self.controls.append(
            ft.Container(
                content=self.content,
                expand=True,
                padding=10,
            )
        )

        # BOTTOM BAR (visible en todos los dispositivos para navegación)
        self.controls.append(self._bottom_bar())

    # ---------- TOP BAR ----------
    def _top_bar(self):
        items = []

        for r in ROUTES:
            if not r.get("show_in_top"):
                continue

            items.append(
                ft.PopupMenuItem(
                    content=ft.Row(
                        controls=[
                            ft.Icon(r["icon"], size=18, color=T.ICON_NEON),
                            ft.Text(
                                I18n.t(r["label"]) if "." in r["label"] else r["label"],
                                size=13
                            ),
                        ],
                        spacing=10,
                    ),
                    on_click=lambda e, p=r["path"]: self.router.navigate(p),
                )
            )

        items.append(ft.PopupMenuItem())  # divider
        items.append(
            ft.PopupMenuItem(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.LOGOUT_ROUNDED, color=T.ICON_NEON_PINK, size=18),
                        ft.Text("Cerrar sesión", color=T.DANGER_TEXT, size=13),
                    ],
                    spacing=10,
                ),
                on_click=self._do_logout,
            )
        )

        user = AppState.current_user
        if user:
            title_widget = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.POINT_OF_SALE_ROUNDED, color=T.ICON_NEON_ALT, size=24),
                    ft.Column(
                        controls=[
                            ft.Text(AppConfig.APP_NAME, size=15, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                f"{user.get('name', user.get('email', ''))}  ·  {user.get('role', 'Admin')}",
                                size=10,
                                color=T.SUCCESS_TEXT,
                            ),
                        ],
                        spacing=0,
                        tight=True,
                    ),
                ],
                spacing=10,
            )
        else:
            title_widget = ft.Text(AppConfig.APP_NAME, size=16, weight=ft.FontWeight.BOLD)

        # Navigation history buttons (back/forward)
        nav_buttons = []
        if self.router.can_go_back():
            nav_buttons.append(
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK_ROUNDED,
                    icon_color=T.ICON_NEON_BLUE,
                    tooltip="Atrás",
                    on_click=lambda e: self.router.go_back(),
                )
            )
        if self.router.can_go_forward():
            nav_buttons.append(
                ft.IconButton(
                    icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                    icon_color=T.ICON_NEON_BLUE,
                    tooltip="Adelante",
                    on_click=lambda e: self.router.go_forward(),
                )
            )

        # Quick action buttons for topbar (solo desktop/tablet)
        quick_actions = []
        if AppState.device != "mobile":
            quick_actions = [
                ft.IconButton(ft.Icons.POINT_OF_SALE_ROUNDED, tooltip="POS", icon_color=T.ICON_NEON, on_click=lambda e: self.router.navigate("/pos")),
                ft.IconButton(ft.Icons.RECEIPT_LONG_ROUNDED, tooltip="Facturas", icon_color=T.ICON_NEON_BLUE, on_click=lambda e: self.router.navigate("/invoices")),
                ft.IconButton(ft.Icons.DESCRIPTION_ROUNDED, tooltip="Cotizaciones", icon_color=T.ICON_NEON_PURPLE, on_click=lambda e: self.router.navigate("/quotations")),
                ft.IconButton(ft.Icons.PEOPLE_ROUNDED, tooltip="Clientes", icon_color=T.ICON_NEON_ALT, on_click=lambda e: self.router.navigate("/clients")),
                ft.IconButton(ft.Icons.INVENTORY_2_ROUNDED, tooltip="Productos", icon_color=T.ICON_NEON_PINK, on_click=lambda e: self.router.navigate("/products")),
                ft.IconButton(ft.Icons.WAREHOUSE_ROUNDED, tooltip="Inventario", icon_color=T.ICON_NEON_YELLOW, on_click=lambda e: self.router.navigate("/inventory")),
                ft.IconButton(ft.Icons.BUSINESS_ROUNDED, tooltip="Empresa", icon_color=T.ICON_NEON_ORANGE, on_click=lambda e: self.router.navigate("/company")),
            ]

        # En móvil, solo mostrar logout y menú
        actions = []
        if quick_actions:
            actions.append(ft.Row(quick_actions, spacing=2))
            actions.append(ft.VerticalDivider(width=1, color=T.BORDER_STRONG))
        actions.append(
            ft.IconButton(
                icon=ft.Icons.LOGOUT_ROUNDED,
                icon_color=T.ICON_NEON_PINK,
                tooltip="Cerrar sesión",
                on_click=self._do_logout,
            )
        )
        actions.append(
            ft.PopupMenuButton(
                icon=ft.Icons.MENU,
                icon_color=T.ICON_NEON,
                items=items,
            )
        )

        return ft.AppBar(
            title=title_widget,
            leading=ft.Row(nav_buttons, spacing=0) if nav_buttons else None,
            actions=actions,
            bgcolor=T.APPBAR_BG,
            color=T.TEXT,
        )

    def _do_logout(self, e=None):
        """Limpia el usuario de AppState y navega al login."""
        AppState.current_user = None
        self.router.navigate("/login", clear_history=True)


    # ---------- BOTTOM BAR ----------
    def _bottom_bar(self):
        destinations = []
        paths = []

        for r in ROUTES:
            if r.get("show_in_bottom"):
                destinations.append(
                    ft.NavigationBarDestination(
                        icon=ft.Icon(r["icon"], color=T.ICON_NEON),
                        selected_icon=ft.Icon(r["icon"], color=T.ICON_NEON_ALT),
                        label=I18n.t(r["label"]) if "." in r["label"] else r["label"],
                    )
                )
                paths.append(r["path"])

        def on_change(e):
            self.router.navigate(paths[e.control.selected_index])

        return ft.NavigationBar(
            bgcolor=T.NAV_BG,
            destinations=destinations,
            selected_index=paths.index(AppState.current_route)
            if AppState.current_route in paths else 0,
            on_change=on_change,
        )
