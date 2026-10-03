import flet as ft
from core.state import AppState
from core.i18n import I18n
from configs.routes import ROUTES

class MainLayout(ft.Column):
    def __init__(self, page, content, router):
        super().__init__(expand=True)
        self._page = page
        self.router = router
        self.content = content

        self._build()

    def _build(self):
        self.controls.clear()

        # TOP BAR
        self.controls.append(self._top_bar())

        # CONTENT
        self.controls.append(
            ft.Container(
                content=self.content,
                expand=True,
                padding=10,
            )
        )

        # BOTTOM BAR (mobile / tablet)
        if AppState.device != "desktop":
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
                            ft.Icon(r["icon"], size=18),
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
                        ft.Icon(ft.Icons.LOGOUT_ROUNDED, color="#ef4444", size=18),
                        ft.Text("Cerrar sesión", color="#ef4444", size=13),
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
                    ft.Icon(ft.Icons.POINT_OF_SALE_ROUNDED, color="#3b82f6", size=24),
                    ft.Column(
                        controls=[
                            ft.Text("FLETING POS & BILLING", size=15, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                f"{user.get('name', user.get('email', ''))}  ·  {user.get('role', 'Admin')}",
                                size=10,
                                color=ft.Colors.GREEN_300,
                            ),
                        ],
                        spacing=0,
                        tight=True,
                    ),
                ],
                spacing=10,
            )
        else:
            title_widget = ft.Text("FLETING POS & BILLING", size=16, weight=ft.FontWeight.BOLD)

        # Quick action buttons for topbar
        quick_actions = [
            ft.IconButton(ft.Icons.POINT_OF_SALE_ROUNDED, tooltip="Punto de Venta (POS)", icon_color="#059669", on_click=lambda e: self.router.navigate("/pos")),
            ft.IconButton(ft.Icons.RECEIPT_LONG_ROUNDED, tooltip="Facturas", icon_color="#3b82f6", on_click=lambda e: self.router.navigate("/invoices")),
            ft.IconButton(ft.Icons.PEOPLE_ROUNDED, tooltip="Clientes", icon_color="#60a5fa", on_click=lambda e: self.router.navigate("/clients")),
            ft.IconButton(ft.Icons.INVENTORY_2_ROUNDED, tooltip="Productos", icon_color="#a855f7", on_click=lambda e: self.router.navigate("/products")),
            ft.IconButton(ft.Icons.BUSINESS_ROUNDED, tooltip="Empresa & Firma", icon_color="#ec4899", on_click=lambda e: self.router.navigate("/company")),
        ]

        return ft.AppBar(
            title=title_widget,
            actions=[
                ft.Row(quick_actions, spacing=2),
                ft.VerticalDivider(width=1, color="#334155"),
                ft.IconButton(
                    icon=ft.Icons.LOGOUT_ROUNDED,
                    icon_color="#ef4444",
                    tooltip="Cerrar sesión",
                    on_click=self._do_logout,
                ),
                ft.PopupMenuButton(
                    icon=ft.Icons.MENU,
                    items=items,
                ),
            ],
        )

    def _do_logout(self, e=None):
        """Limpia el usuario de AppState y navega al login."""
        AppState.current_user = None
        self.router.navigate("/login")


    # ---------- BOTTOM BAR ----------
    def _bottom_bar(self):
        destinations = []
        paths = []

        for r in ROUTES:
            if r.get("show_in_bottom"):
                destinations.append(
                    ft.NavigationBarDestination(
                        icon=r["icon"],
                        label=I18n.t(r["label"]) if "." in r["label"] else r["label"],
                    )
                )
                paths.append(r["path"])

        def on_change(e):
            self.router.navigate(paths[e.control.selected_index])

        return ft.NavigationBar(
            destinations=destinations,
            selected_index=paths.index(AppState.current_route)
            if AppState.current_route in paths else 0,
            on_change=on_change,
        )
