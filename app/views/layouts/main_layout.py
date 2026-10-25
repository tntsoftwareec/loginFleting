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

    def _can_access(self, route_def) -> bool:
        """True si el rol actual puede leer el módulo de la ruta."""
        module = route_def.get("module")
        return not module or AppState.can_access_module(module)

    # ---------- TOP BAR ----------
    def _top_bar(self):
        items = []

        for r in ROUTES:
            if not r.get("show_in_top") or not self._can_access(r):
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
            quick_defs = [
                (ft.Icons.POINT_OF_SALE_ROUNDED, "POS", T.ICON_NEON, "/pos"),
                (ft.Icons.RECEIPT_LONG_ROUNDED, "Facturas", T.ICON_NEON_BLUE, "/invoices"),
                (ft.Icons.DESCRIPTION_ROUNDED, "Cotizaciones", T.ICON_NEON_PURPLE, "/quotations"),
                (ft.Icons.PEOPLE_ROUNDED, "Clientes", T.ICON_NEON_ALT, "/clients"),
                (ft.Icons.INVENTORY_2_ROUNDED, "Productos", T.ICON_NEON_PINK, "/products"),
                (ft.Icons.WAREHOUSE_ROUNDED, "Inventario", T.ICON_NEON_YELLOW, "/inventory"),
                (ft.Icons.BUSINESS_ROUNDED, "Empresa", T.ICON_NEON_ORANGE, "/company"),
            ]
            route_by_path = {r["path"]: r for r in ROUTES}
            quick_actions = [
                ft.IconButton(
                    icon,
                    tooltip=tooltip,
                    icon_color=color,
                    on_click=lambda e, path=path: self.router.navigate(path),
                )
                for icon, tooltip, color, path in quick_defs
                if self._can_access(route_by_path.get(path, {}))
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
            if r.get("show_in_bottom") and self._can_access(r):
                destinations.append(
                    ft.NavigationBarDestination(
                        icon=ft.Icon(r["icon"], color=T.ICON_NEON),
                        selected_icon=ft.Icon(r["icon"], color=T.ICON_NEON_ALT),
                        label=I18n.t(r["label"]) if "." in r["label"] else r["label"],
                    )
                )
                paths.append(r["path"])

        # Un rol puede no tener ninguna ruta en la barra inferior.
        if not destinations:
            return ft.Container(height=0)

        def on_change(e):
            self.router.navigate(paths[e.control.selected_index])

        return ft.NavigationBar(
            bgcolor=T.NAV_BG,
            destinations=destinations,
            selected_index=paths.index(AppState.current_route)
            if AppState.current_route in paths else 0,
            on_change=on_change,
        )
