import flet as ft
from app.views.layouts.main_layout import MainLayout
from core.state import AppState

def _all_border(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)

class HomeView:
    def __init__(self, page, router):
        self.page = page
        self.router = router

    def render(self):
        user = AppState.current_user or {}
        user_name = user.get("name", "Usuario")

        modules = [
            {
                "title": "Punto de Venta (POS)",
                "desc": "Emisión de facturas electrónicas, carritos de venta y cobro en caja",
                "icon": ft.Icons.POINT_OF_SALE_ROUNDED,
                "color": "#059669",
                "route": "/pos"
            },
            {
                "title": "Facturas Emitidas",
                "desc": "Consulta de comprobantes, descarga de XML y RIDE PDF, re-envío por correo",
                "icon": ft.Icons.RECEIPT_LONG_ROUNDED,
                "color": "#2563eb",
                "route": "/invoices"
            },
            {
                "title": "Directorio de Clientes",
                "desc": "Gestión CRUD de clientes, RUC/Cédula, correo y teléfonos",
                "icon": ft.Icons.PEOPLE_ROUNDED,
                "color": "#0284c7",
                "route": "/clients"
            },
            {
                "title": "Gestión de Proveedores",
                "desc": "Control de distribuidores, marcas y personas de contacto",
                "icon": ft.Icons.LOCAL_SHIPPING_ROUNDED,
                "color": "#10b981",
                "route": "/suppliers"
            },
            {
                "title": "Catálogo de Productos",
                "desc": "Inventario de mercancías, control de precios, costos y stock",
                "icon": ft.Icons.INVENTORY_2_ROUNDED,
                "color": "#a855f7",
                "route": "/products"
            },
            {
                "title": "Servicios Ofrecidos",
                "desc": "Tarifas de servicios, consultorías y soporte técnico",
                "icon": ft.Icons.MISCELLANEOUS_SERVICES_ROUNDED,
                "color": "#06b6d4",
                "route": "/services"
            },
            {
                "title": "Datos de Empresa & Firma",
                "desc": "Parámetros del negocio, RUC, firma digital .p12 y correo SMTP",
                "icon": ft.Icons.BUSINESS_ROUNDED,
                "color": "#ec4899",
                "route": "/company"
            },
            {
                "title": "Usuarios y Permisos",
                "desc": "Administración de accesos de personal, cajeros y roles del sistema",
                "icon": ft.Icons.SUPERVISED_USER_CIRCLE_ROUNDED,
                "color": "#6366f1",
                "route": "/users"
            },
        ]

        cards = []
        for m in modules:
            card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Icon(m["icon"], size=24, color="#ffffff"),
                                    bgcolor=m["color"],
                                    padding=10,
                                    border_radius=8,
                                ),
                                ft.Text(m["title"], size=15, weight=ft.FontWeight.BOLD, color="#f8fafc"),
                            ],
                            spacing=12,
                        ),
                        ft.Text(m["desc"], size=12, color="#94a3b8"),
                        ft.Row(
                            controls=[
                                ft.TextButton(
                                    "Acceder al módulo",
                                    icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                                    style=ft.ButtonStyle(color=m["color"]),
                                    on_click=lambda e, r=m["route"]: self.router.navigate(r),
                                )
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                    spacing=10,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=16,
                bgcolor="#0f172a",
                border_radius=10,
                border=_all_border(1, "#1e293b"),
                width=340,
                height=160,
            )
            cards.append(card)

        grid_cards = ft.Row(
            controls=cards,
            wrap=True,
            spacing=16,
            run_spacing=16,
        )

        header_welcome = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(f"¡Bienvenido de nuevo, {user_name}!", size=24, weight=ft.FontWeight.BOLD, color="#f8fafc"),
                    ft.Text("Sistema Integrado de Facturación Electrónica SRI Ecuador y Punto de Venta (POS)", size=14, color="#94a3b8"),
                ],
                spacing=4,
            ),
            padding=16,
            bgcolor="#0f172a",
            border_radius=10,
            border=_all_border(1, "#1e293b"),
        )

        content = ft.Column(
            controls=[
                header_welcome,
                ft.Container(height=10),
                grid_cards,
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )

        return MainLayout(
            page=self.page,
            content=content,
            router=self.router,
        )
