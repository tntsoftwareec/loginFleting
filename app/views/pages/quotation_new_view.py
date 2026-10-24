import os
import flet as ft
from core import theme as T
from app.views.layouts.main_layout import MainLayout
from app.views.ui_helpers import (
    open_manual_service_dialog,
    open_path,
    send_whatsapp_document,
)
from app.controllers.client_controller import ClientController
from app.controllers.product_controller import ProductController
from app.controllers.service_controller import ServiceController
from app.controllers.quotation_controller import QuotationController
from app.models.company_model import CompanyModel
from app.services.whatsapp_service import build_quote_message, build_whatsapp_link
from core.state import AppState

def _all_border(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)

class QuotationNewView:
    """Vista de creación de cotización — interfaz similar al POS pero sin emitir factura."""
    def __init__(self, page: ft.Page, router):
        self.page = page
        self.router = router
        self.clients_list = []
        self.products_list = []
        self.services_list = []
        self.selected_client_id = None
        self.cart_items = []
        self.catalog_tab = "productos"
        self.search_catalog = ""

    def render(self):
        if not AppState.has_permission("can_read"):
            content_layout = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.LOCK_OUTLINED, color=T.DANGER, size=64),
                        ft.Text("Acceso Restringido", color=T.TEXT, size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("No tienes permisos suficientes para acceder a este módulo.", color=T.TEXT_MUTED, size=14),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12,
                ),
                padding=60,
                alignment=ft.Alignment(0, 0),
                expand=True,
            )
            return MainLayout(page=self.page, content=content_layout, router=self.router)

        def show_dialog(dlg):
            self.page.dialog = dlg
            dlg.open = True
            if hasattr(self.page, "show_dialog"):
                try:
                    self.page.show_dialog(dlg)
                    return
                except Exception:
                    pass
            self.page.update()

        def close_dialog(dlg):
            dlg.open = False
            if hasattr(self.page, "pop_dialog"):
                try:
                    self.page.pop_dialog()
                except Exception:
                    pass
            self.page.update()

        def show_toast(message: str, is_error: bool = False):
            snack = ft.SnackBar(
                content=ft.Text(message, color=T.ON_ACCENT),
                bgcolor=T.DANGER if is_error else T.SUCCESS,
                duration=3500,
            )
            if hasattr(self.page, "show_dialog"):
                self.page.show_dialog(snack)
            else:
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()

        self.catalog_container = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        self.cart_container = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)

        txt_sub15 = ft.Text("$0.00", size=13, weight=ft.FontWeight.BOLD, color=T.TEXT)
        txt_sub0 = ft.Text("$0.00", size=13, weight=ft.FontWeight.BOLD, color=T.TEXT)
        txt_desc = ft.Text("$0.00", size=13, weight=ft.FontWeight.BOLD, color=T.TEXT)
        txt_iva = ft.Text("$0.00", size=13, weight=ft.FontWeight.BOLD, color=T.TEXT)
        txt_total = ft.Text("$0.00", size=18, weight=ft.FontWeight.BOLD, color=T.SUCCESS_TEXT)

        tf_notas = ft.TextField(
            label="Notas / Observaciones",
            hint_text="Ej: Válida por 15 días, condiciones de entrega...",
            multiline=True,
            min_lines=2,
            max_lines=4,
            expand=True,
        )

        tf_dias_validez = ft.TextField(
            label="Días de Validez",
            value="15",
            width=100,
            height=42,
            text_size=13,
            content_padding=ft.Padding.symmetric(horizontal=8, vertical=0),
        )

        dd_client = ft.Dropdown(
            label="Seleccionar Cliente",
            hint_text="Buscar cliente...",
            expand=True,
        )

        def on_client_changed(e):
            val = getattr(e, 'data', None) or (dd_client.value if dd_client.value else None)
            if val:
                self.selected_client_id = int(val)

        dd_client.on_select = on_client_changed

        def load_initial_data():
            self.clients_list = ClientController.get_all()
            self.products_list = ProductController.get_all()
            self.services_list = ServiceController.get_all()

            client_options = []
            for c in self.clients_list:
                label = f"{c['identificacion']} - {c['razon_social']}"
                client_options.append(ft.dropdown.Option(str(c["id"]), label))

            dd_client.options = client_options
            if self.clients_list and not self.selected_client_id:
                # Don't default to Consumidor Final for quotations — require explicit selection
                self.selected_client_id = self.clients_list[0]['id']
                dd_client.value = str(self.selected_client_id)

            pending = getattr(AppState, "pending_cart_items", None)
            if pending:
                self.cart_items = [dict(item) for item in pending]
                AppState.pending_cart_items = None

            render_catalog()
            render_cart()

        def render_catalog():
            self.catalog_container.controls.clear()

            items_to_show = self.products_list if self.catalog_tab == "productos" else self.services_list
            q = self.search_catalog.lower()

            filtered = []
            for item in items_to_show:
                matches = (
                    not q or
                    q in item["codigo"].lower() or
                    q in item["nombre"].lower() or
                    q in (item.get("categoria") or "").lower()
                )
                if matches and item.get("status", "active") == "active":
                    filtered.append(item)

            if not filtered:
                self.catalog_container.controls.append(
                    ft.Container(
                        content=ft.Text("No hay ítems disponibles", color=T.TEXT_MUTED, size=13),
                        padding=20,
                        alignment=ft.Alignment(0, 0)
                    )
                )
                self.page.update()
                return

            for it in filtered:
                is_prod = self.catalog_tab == "productos"
                code = it["codigo"]
                name = it["nombre"]
                price = float(it["precio"])
                stock = int(it.get("stock", 0)) if is_prod else None
                iva_p = float(it.get("iva_porcentaje", 15.0))

                stock_str = f"Stock: {stock}" if is_prod else "Servicio"
                stock_color = T.SUCCESS_TEXT if not is_prod or stock > 5 else (T.WARNING if stock > 0 else T.DANGER_TEXT)

                card_item = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.INVENTORY_2_OUTLINED if is_prod else ft.Icons.HANDYMAN_OUTLINED, color=T.PURPLE if is_prod else T.CYAN_TEXT, size=22),
                            ft.Column(
                                controls=[
                                    ft.Text(f"{code} · {name}", size=13, weight=ft.FontWeight.BOLD, color=T.TEXT, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Row(
                                        controls=[
                                            ft.Text(f"${price:.2f}", size=12, weight=ft.FontWeight.BOLD, color=T.SUCCESS_TEXT),
                                            ft.Text(f"IVA {iva_p:.0f}%", size=10, color=T.TEXT_MUTED),
                                            ft.Text(stock_str, size=10, color=stock_color, weight=ft.FontWeight.BOLD),
                                        ],
                                        spacing=8,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.ADD_CIRCLE_ROUNDED,
                                icon_color=T.PURPLE_BTN,
                                tooltip="Agregar a la cotización",
                                on_click=lambda e, item=it, tp=("producto" if is_prod else "servicio"): add_to_cart(item, tp),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=10,
                    bgcolor=T.SURFACE_ALT,
                    border_radius=8,
                    border=_all_border(1, T.BORDER_STRONG),
                )
                self.catalog_container.controls.append(card_item)

            self.page.update()

        def add_to_cart(item: dict, tipo: str):
            item_id = item["id"]
            # Los servicios manuales tienen id=None y cada uno debe ser una
            # línea independiente; no se agrupan entre sí.
            existing = []
            if item_id is not None:
                existing = [c for c in self.cart_items if c["id"] == item_id and c["tipo"] == tipo]
            if existing:
                existing[0]["cantidad"] += 1
            else:
                self.cart_items.append({
                    "id": item_id,
                    "tipo": tipo,
                    "codigo": item["codigo"],
                    "nombre": item["nombre"],
                    "precio": float(item["precio"]),
                    "cantidad": 1,
                    "descuento": 0.0,
                    "iva_porcentaje": float(item.get("iva_porcentaje", 15.0)),
                    "imagen_path": item.get("imagen_path", "") if tipo == "producto" else "",
                })
            render_cart()
            show_toast(f"'{item['nombre']}' agregado a la cotización.")

        def add_manual_service(item: dict):
            self.cart_items.append(item)
            render_cart()
            show_toast(f"Servicio '{item['nombre']}' agregado a la cotización.")

        def update_qty(index: int, delta: float):
            if 0 <= index < len(self.cart_items):
                self.cart_items[index]["cantidad"] += delta
                if self.cart_items[index]["cantidad"] <= 0:
                    self.cart_items.pop(index)
                render_cart()

        def remove_item(index: int):
            if 0 <= index < len(self.cart_items):
                self.cart_items.pop(index)
                render_cart()

        def update_discount(index: int, val_str: str):
            try:
                d = float(val_str)
                if 0 <= index < len(self.cart_items):
                    self.cart_items[index]["descuento"] = max(0.0, d)
                    recalculate_totals()
            except ValueError:
                pass

        def render_cart():
            self.cart_container.controls.clear()

            if not self.cart_items:
                self.cart_container.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=40, color=T.ICON_MUTED),
                                ft.Text("Agregue ítems a la cotización", color=T.TEXT_MUTED, size=13),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=6,
                        ),
                        padding=30,
                        alignment=ft.Alignment(0, 0),
                    )
                )
                recalculate_totals()
                self.page.update()
                return

            for idx, item in enumerate(self.cart_items):
                qty = item["cantidad"]
                price = item["precio"]
                desc = item["descuento"]
                sub = (qty * price) - desc
                iva_val = (sub * (item["iva_porcentaje"] / 100.0)) if item["iva_porcentaje"] > 0 else 0.0
                total_i = sub + iva_val

                row_cart = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(f"{item['codigo']} - {item['nombre']}", size=12, weight=ft.FontWeight.BOLD, color=T.TEXT, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text(f"P.Unit: ${price:.2f} | Total: ${total_i:.2f}", size=11, color=T.TEXT_MUTED),
                                ],
                                spacing=1,
                                expand=True,
                            ),
                            ft.Row(
                                controls=[
                                    ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINED, icon_size=18, icon_color=T.DANGER_TEXT, on_click=lambda e, i=idx: update_qty(i, -1)),
                                    ft.Text(f"{int(qty) if qty == int(qty) else qty:.1f}", size=12, weight=ft.FontWeight.BOLD),
                                    ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINED, icon_size=18, icon_color=T.SUCCESS_TEXT, on_click=lambda e, i=idx: update_qty(i, 1)),
                                ],
                                spacing=0,
                            ),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE_ROUNDED, icon_size=18, icon_color=T.DANGER, on_click=lambda e, i=idx: remove_item(i)),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=8,
                    bgcolor=T.SURFACE_ALT,
                    border_radius=6,
                )
                self.cart_container.controls.append(row_cart)

            recalculate_totals()
            self.page.update()

        def recalculate_totals():
            sub15 = 0.0
            sub0 = 0.0
            total_d = 0.0
            iva_t = 0.0

            for item in self.cart_items:
                q = item["cantidad"]
                p = item["precio"]
                d = item["descuento"]
                sub = (q * p) - d
                iva_p = item["iva_porcentaje"]

                total_d += d
                if iva_p > 0:
                    sub15 += sub
                    iva_t += sub * (iva_p / 100.0)
                else:
                    sub0 += sub

            txt_sub15.value = f"${sub15:.2f}"
            txt_sub0.value = f"${sub0:.2f}"
            txt_desc.value = f"${total_d:.2f}"
            txt_iva.value = f"${iva_t:.2f}"
            txt_total.value = f"${sub15 + sub0 + iva_t:.2f}"

        def open_quick_client_dialog():
            tf_ident = ft.TextField(label="Identificación / RUC", expand=True)
            tf_razon = ft.TextField(label="Razón Social / Nombre", expand=True)
            tf_email = ft.TextField(label="Correo Electrónico", expand=True)

            def save_quick_client(e):
                success, res = ClientController.create(
                    tipo_documento="CEDULA" if len(tf_ident.value or "") == 10 else "RUC",
                    identificacion=tf_ident.value,
                    razon_social=tf_razon.value,
                    email=tf_email.value
                )
                if success:
                    close_dialog(dlg)
                    show_toast("Cliente registrado y seleccionado.")
                    self.selected_client_id = res["id"]
                    load_initial_data()
                else:
                    show_toast(res, is_error=True)

            dlg = ft.AlertDialog(
                title=ft.Text("Registrar Cliente Rápido", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column([tf_ident, tf_razon, tf_email], tight=True, spacing=10),
                    width=400,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg)),
                    ft.FilledButton("Guardar", style=ft.ButtonStyle(bgcolor=T.PRIMARY, color=T.ON_ACCENT), on_click=save_quick_client),
                ],
            )
            show_dialog(dlg)

        def emit_quotation(e):
            can_write = AppState.has_permission("can_write")
            if not can_write:
                show_toast("No tienes permisos para crear cotizaciones.", is_error=True)
                return

            if not self.cart_items:
                show_toast("La lista está vacía. Agregue productos o servicios.", is_error=True)
                return

            if not self.selected_client_id:
                show_toast("Seleccione un cliente para generar la cotización.", is_error=True)
                return

            try:
                dias = int(tf_dias_validez.value or "15")
            except ValueError:
                dias = 15

            try:
                success, result = QuotationController.create_quotation(
                    client_id=self.selected_client_id,
                    cart_items=self.cart_items,
                    notas=tf_notas.value or "",
                    dias_validez=dias,
                )
            except Exception as ex:
                show_toast(f"Error inesperado: {ex}", is_error=True)
                return

            if not success:
                show_toast(result, is_error=True)
                return

            secuencial = result.get("secuencial")
            pdf_path = result.get("pdf_path")
            quot_id = result.get("id")

            def open_pdf(ev):
                open_path(self.page, pdf_path)

            def send_email_now(ev):
                close_dialog(dlg)
                show_toast("Enviando cotización por correo...")
                ok, msg = QuotationController.send_quotation_email(quot_id)
                if ok:
                    show_toast(msg)
                else:
                    show_toast(msg, is_error=True)

            def send_whatsapp_now(ev):
                client = ClientController.get_by_id(
                    result.get("client_id") or self.selected_client_id
                ) if (result.get("client_id") or self.selected_client_id) else None
                phone = (client or {}).get("telefono") or ""
                if not phone:
                    show_toast(
                        "El cliente no tiene un teléfono registrado para WhatsApp.",
                        is_error=True,
                    )
                    return

                full = QuotationController.get_by_id(quot_id) or result
                pdf = QuotationController.ensure_quotation_pdf(quot_id) or pdf_path
                if not pdf:
                    show_toast(
                        "No se pudo generar el PDF de la cotización.",
                        is_error=True,
                    )
                    return

                company = CompanyModel.get_info() or {}
                empresa = company.get("razon_social") or "Nuestra empresa"
                message = build_quote_message(full, full.get("items") or [], empresa)
                link = build_whatsapp_link(phone, message)
                close_dialog(dlg)
                send_whatsapp_document(
                    self.page,
                    link=link,
                    pdf_path=pdf,
                    message=message,
                    on_sent=lambda: QuotationController.mark_whatsapp_sent(quot_id),
                )

            def go_to_list(ev):
                close_dialog(dlg)
                self.router.navigate("/quotations")

            def new_quotation(ev):
                close_dialog(dlg)
                self.cart_items = []
                self.selected_client_id = None
                tf_notas.value = ""
                tf_dias_validez.value = "15"
                load_initial_data()
                show_toast("Listo para crear una nueva cotización.")

            dlg = ft.AlertDialog(
                title=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINED, color=T.SUCCESS_TEXT, size=28),
                        ft.Text("Cotización Generada Exitosamente", weight=ft.FontWeight.BOLD, color=T.SUCCESS_TEXT),
                    ],
                    spacing=10,
                ),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(f"N° Cotización: {secuencial}", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text(f"Total: ${float(result.get('importe_total', 0)):.2f}", size=13, color=T.SUCCESS_TEXT),
                            ft.Divider(height=1),
                            ft.Text("¿Desea enviar la cotización al cliente?", size=13, color=T.TEXT_MUTED),
                        ],
                        tight=True,
                        spacing=10,
                    ),
                    width=450,
                ),
                actions=[
                    ft.OutlinedButton("Ver Historial", icon=ft.Icons.LIST_ROUNDED, on_click=go_to_list),
                    ft.FilledButton("Abrir PDF", icon=ft.Icons.PICTURE_IN_PICTURE_ROUNDED, style=ft.ButtonStyle(bgcolor=T.PRIMARY, color=T.ON_ACCENT), on_click=open_pdf),
                    ft.FilledButton("Enviar por Correo", icon=ft.Icons.EMAIL_OUTLINED, style=ft.ButtonStyle(bgcolor=T.SUCCESS_STRONG, color=T.ON_ACCENT), on_click=send_email_now),
                    ft.FilledButton("Enviar por WhatsApp", icon=ft.Icons.CHAT_OUTLINED, style=ft.ButtonStyle(bgcolor=T.WHATSAPP, color=T.ON_ACCENT), on_click=send_whatsapp_now),
                    ft.FilledButton("Nueva Cotización", icon=ft.Icons.ADD_ROUNDED, style=ft.ButtonStyle(bgcolor=T.PURPLE_BTN, color=T.ON_ACCENT), on_click=new_quotation),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            show_dialog(dlg)

        def set_tab(tab_name: str):
            self.catalog_tab = tab_name
            btn_tab_prod.style = ft.ButtonStyle(
                bgcolor=T.PURPLE_BTN if tab_name == "productos" else T.SURFACE_ALT,
                color=T.ON_ACCENT if tab_name == "productos" else T.TEXT,
            )
            btn_tab_serv.style = ft.ButtonStyle(
                bgcolor=T.PURPLE_BTN if tab_name == "servicios" else T.SURFACE_ALT,
                color=T.ON_ACCENT if tab_name == "servicios" else T.TEXT,
            )
            render_catalog()

        btn_tab_prod = ft.FilledButton(
            "Productos",
            icon=ft.Icons.INVENTORY_2_OUTLINED,
            style=ft.ButtonStyle(bgcolor=T.PURPLE_BTN, color=T.ON_ACCENT),
            on_click=lambda e: set_tab("productos"),
            expand=True,
            height=38,
        )
        btn_tab_serv = ft.FilledButton(
            "Servicios",
            icon=ft.Icons.HANDYMAN_OUTLINED,
            style=ft.ButtonStyle(bgcolor=T.SURFACE_ALT, color=T.TEXT),
            on_click=lambda e: set_tab("servicios"),
            expand=True,
            height=38,
        )
        btn_manual_service = ft.IconButton(
            icon=ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED,
            icon_color=T.CYAN_TEXT,
            tooltip="Agregar servicio manual (sin catálogo)",
            on_click=lambda e: open_manual_service_dialog(self.page, add_manual_service),
            height=38,
        )

        def on_search(e):
            self.search_catalog = e.control.value
            render_catalog()

        search_catalog_tf = ft.TextField(
            hint_text="Buscar ítem por código o nombre...",
            prefix_icon=ft.Icons.SEARCH,
            height=40,
            text_size=13,
            content_padding=ft.Padding.symmetric(horizontal=8, vertical=0),
            on_change=on_search,
        )

        left_catalog_panel = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK_ROUNDED,
                                icon_color=T.ICON_NEON_BLUE,
                                tooltip="Volver al historial",
                                on_click=lambda e: self.router.navigate("/quotations"),
                            ),
                            ft.Text("Catálogo de Ítems", size=15, weight=ft.FontWeight.BOLD, color=T.TEXT),
                        ],
                        spacing=4,
                    ),
                    ft.Row([btn_tab_prod, btn_tab_serv, btn_manual_service], spacing=8),
                    search_catalog_tf,
                    self.catalog_container,
                ],
                spacing=10,
                expand=True,
            ),
            padding=12,
            bgcolor=T.SURFACE,
            border_radius=10,
            border=_all_border(1, T.SURFACE_ALT),
            expand=5,
        )

        right_cart_panel = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.DESCRIPTION_ROUNDED, size=22, color=T.PURPLE_TEXT),
                            ft.Text("Nueva Cotización", size=15, weight=ft.FontWeight.BOLD, color=T.TEXT),
                        ],
                        spacing=8,
                    ),
                    ft.Row(
                        controls=[
                            dd_client,
                            ft.IconButton(
                                icon=ft.Icons.PERSON_ADD_ROUNDED,
                                icon_color=T.INFO,
                                tooltip="Nuevo Cliente Rápido",
                                on_click=lambda e: open_quick_client_dialog(),
                            ),
                        ],
                        spacing=4,
                    ),
                    ft.Text("Detalle de la Cotización", size=13, weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED),
                    self.cart_container,
                    ft.Divider(height=1, color=T.BORDER_STRONG),
                    ft.Column(
                        controls=[
                            ft.Row([ft.Text("Subtotal IVA 15%:", size=12, color=T.TEXT_MUTED), txt_sub15], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("Subtotal 0%:", size=12, color=T.TEXT_MUTED), txt_sub0], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("Total Descuento:", size=12, color=T.TEXT_MUTED), txt_desc], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("Monto IVA (15%):", size=12, color=T.TEXT_MUTED), txt_iva], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(height=1, color=T.BORDER_STRONG),
                            ft.Row([ft.Text("TOTAL:", size=15, weight=ft.FontWeight.BOLD, color=T.TEXT), txt_total], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ],
                        spacing=4,
                    ),
                    ft.Row(
                        controls=[
                            tf_dias_validez,
                            tf_notas,
                        ],
                        spacing=8,
                    ),
                    ft.FilledButton(
                        "GENERAR COTIZACIÓN",
                        icon=ft.Icons.DESCRIPTION_ROUNDED,
                        style=ft.ButtonStyle(bgcolor=T.PURPLE_BTN, color=T.ON_ACCENT),
                        height=46,
                        on_click=emit_quotation,
                    ),
                ],
                spacing=10,
                expand=True,
            ),
            padding=12,
            bgcolor=T.SURFACE,
            border_radius=10,
            border=_all_border(1, T.SURFACE_ALT),
            expand=4,
        )

        # Responsive: en móvil, una sola columna con scroll
        is_mobile = AppState.device == "mobile"
        if is_mobile:
            main_content = ft.Column(
                controls=[left_catalog_panel, right_cart_panel],
                spacing=12,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            )
        else:
            main_content = ft.Row(
                controls=[left_catalog_panel, right_cart_panel],
                spacing=12,
                expand=True,
            )

        load_initial_data()
        return MainLayout(page=self.page, content=main_content, router=self.router)
