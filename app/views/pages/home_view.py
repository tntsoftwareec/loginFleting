import flet as ft
from core import theme as T
from app.views.layouts.main_layout import MainLayout
from app.views.ui_helpers import stat_card
from app.controllers.client_controller import ClientController
from app.controllers.product_controller import ProductController
from app.controllers.inventory_controller import InventoryController
from app.controllers.invoice_controller import InvoiceController
from app.controllers.quotation_controller import QuotationController
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
                "color": T.SUCCESS_STRONG,
                "route": "/pos"
            },
            {
                "title": "Facturas Emitidas",
                "desc": "Consulta de comprobantes, descarga de XML y RIDE PDF, re-envío por correo",
                "icon": ft.Icons.RECEIPT_LONG_ROUNDED,
                "color": T.PRIMARY,
                "route": "/invoices"
            },
            {
                "title": "Directorio de Clientes",
                "desc": "Gestión CRUD de clientes, RUC/Cédula, correo y teléfonos",
                "icon": ft.Icons.PEOPLE_ROUNDED,
                "color": T.SKY,
                "route": "/clients"
            },
            {
                "title": "Gestión de Proveedores",
                "desc": "Control de distribuidores, marcas y personas de contacto",
                "icon": ft.Icons.LOCAL_SHIPPING_ROUNDED,
                "color": T.SUCCESS,
                "route": "/suppliers"
            },
            {
                "title": "Catálogo de Productos",
                "desc": "Precios, costos, imágenes y datos del catálogo de mercancías",
                "icon": ft.Icons.INVENTORY_2_ROUNDED,
                "color": T.PURPLE,
                "route": "/products"
            },
            {
                "title": "Inventario y Existencias",
                "desc": "Entradas, salidas, ajustes de stock, alertas e historial de movimientos",
                "icon": ft.Icons.WAREHOUSE_ROUNDED,
                "color": T.WARNING,
                "route": "/inventory"
            },
            {
                "title": "Servicios Ofrecidos",
                "desc": "Tarifas de servicios, consultorías y soporte técnico",
                "icon": ft.Icons.MISCELLANEOUS_SERVICES_ROUNDED,
                "color": T.CYAN,
                "route": "/services"
            },
            {
                "title": "Datos de Empresa & Firma",
                "desc": "Parámetros del negocio, RUC, firma digital .p12 y correo SMTP",
                "icon": ft.Icons.BUSINESS_ROUNDED,
                "color": T.PINK,
                "route": "/company"
            },
            {
                "title": "Usuarios y Permisos",
                "desc": "Administración de accesos de personal, cajeros y roles del sistema",
                "icon": ft.Icons.SUPERVISED_USER_CIRCLE_ROUNDED,
                "color": T.INDIGO,
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
                                    content=ft.Icon(m["icon"], size=24, color=T.ON_ACCENT),
                                    bgcolor=m["color"],
                                    padding=10,
                                    border_radius=8,
                                ),
                                ft.Text(m["title"], size=15, weight=ft.FontWeight.BOLD, color=T.TEXT),
                            ],
                            spacing=12,
                        ),
                        ft.Text(m["desc"], size=12, color=T.TEXT_MUTED),
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
                bgcolor=T.SURFACE,
                border_radius=10,
                border=_all_border(1, T.SURFACE_ALT),
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
                    ft.Text(f"¡Bienvenido de nuevo, {user_name}!", size=24, weight=ft.FontWeight.BOLD, color=T.TEXT),
                    ft.Text("Sistema Integrado de Facturación Electrónica SRI Ecuador y Punto de Venta (POS)", size=14, color=T.TEXT_MUTED),
                ],
                spacing=4,
            ),
            padding=16,
            bgcolor=T.SURFACE,
            border_radius=10,
            border=_all_border(1, T.SURFACE_ALT),
        )

        # ── Tarjetas de resumen (estadísticas) ──────────────────────────────
        stats_row = ft.ResponsiveRow(spacing=10, run_spacing=10)
        try:
            clientes = len(ClientController.get_all())
            productos = len(ProductController.get_all())
            inventory_summary = InventoryController.get_summary()
            facturas = InvoiceController.get_all()
            cotizaciones = len(QuotationController.get_all())
            facturado = sum(float(f.get("importe_total") or 0) for f in facturas)
            stats_row.controls = [
                stat_card("Clientes", str(clientes), ft.Icons.PEOPLE_ROUNDED, T.SKY),
                stat_card(
                    "Productos",
                    str(productos),
                    ft.Icons.INVENTORY_2_ROUNDED,
                    T.PURPLE,
                    subtitle=f'{inventory_summary["low_stock_total"]} bajo stock',
                ),
                stat_card("Facturas emitidas", str(len(facturas)), ft.Icons.RECEIPT_LONG_ROUNDED,
                          T.PRIMARY, subtitle=f"Total ${facturado:,.2f}"),
                stat_card("Cotizaciones", str(cotizaciones), ft.Icons.DESCRIPTION_ROUNDED, T.PURPLE_TEXT),
            ]
        except Exception:  # noqa: BLE001
            stats_row.controls = []

        content = ft.Column(
            controls=[
                header_welcome,
                ft.Container(height=4),
                stats_row,
                ft.Container(height=8),
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
