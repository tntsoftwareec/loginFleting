import os
import flet as ft
from app.views.layouts.main_layout import MainLayout
from app.controllers.client_controller import ClientController
from app.controllers.product_controller import ProductController
from app.controllers.service_controller import ServiceController
from app.controllers.invoice_controller import InvoiceController
from core.state import AppState

def _all_border(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)

class POSView:
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
                        ft.Icon(ft.Icons.LOCK_OUTLINED, color="#ef4444", size=64),
                        ft.Text("Acceso Restringido", color="#f8fafc", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("No tienes permisos suficientes para acceder a este módulo.", color="#94a3b8", size=14),
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
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message, color="#ffffff"),
                bgcolor="#ef4444" if is_error else "#10b981",
                duration=3500
            )
            self.page.snack_bar.open = True
            self.page.update()

        self.catalog_container = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        self.cart_container = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)

        txt_sub15 = ft.Text("$0.00", size=13, weight=ft.FontWeight.BOLD, color="#f8fafc")
        txt_sub0 = ft.Text("$0.00", size=13, weight=ft.FontWeight.BOLD, color="#f8fafc")
        txt_desc = ft.Text("$0.00", size=13, weight=ft.FontWeight.BOLD, color="#f8fafc")
        txt_iva = ft.Text("$0.00", size=13, weight=ft.FontWeight.BOLD, color="#f8fafc")
        txt_total = ft.Text("$0.00", size=18, weight=ft.FontWeight.BOLD, color="#34d399")

        dd_payment = ft.Dropdown(
            label="Forma de Pago",
            value="EFECTIVO",
            options=[
                ft.dropdown.Option("EFECTIVO", "Efectivo / Sin sistema fin."),
                ft.dropdown.Option("TARJETA", "Tarjeta de Crédito / Débito"),
                ft.dropdown.Option("TRANSFERENCIA", "Transferencia Bancaria"),
            ],
            expand=True,
        )

        dd_client = ft.Dropdown(
            label="Seleccionar Cliente",
            hint_text="Buscar cliente...",
            expand=True,
        )

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
                cf = [c for c in self.clients_list if c['identificacion'] == '9999999999999']
                if cf:
                    self.selected_client_id = cf[0]['id']
                else:
                    self.selected_client_id = self.clients_list[0]['id']
                dd_client.value = str(self.selected_client_id)

            render_catalog()
            render_cart()

        def on_client_changed(e):
            if dd_client.value:
                self.selected_client_id = int(dd_client.value)

        dd_client.on_change = on_client_changed

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
                        content=ft.Text("No hay ítems disponibles", color="#94a3b8", size=13),
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
                stock_color = "#34d399" if not is_prod or stock > 5 else ("#fbbf24" if stock > 0 else "#f87171")

                card_item = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.INVENTORY_2_OUTLINED if is_prod else ft.Icons.HANDYMAN_OUTLINED, color="#a855f7" if is_prod else "#38bdf8", size=22),
                            ft.Column(
                                controls=[
                                    ft.Text(f"{code} · {name}", size=13, weight=ft.FontWeight.BOLD, color="#f8fafc", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Row(
                                        controls=[
                                            ft.Text(f"${price:.2f}", size=12, weight=ft.FontWeight.BOLD, color="#34d399"),
                                            ft.Text(f"IVA {iva_p:.0f}%", size=10, color="#94a3b8"),
                                            ft.Text(stock_str, size=10, color=stock_color, weight=ft.FontWeight.BOLD),
                                        ],
                                        spacing=8,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.ADD_SHOPPING_CART_ROUNDED,
                                icon_color="#3b82f6",
                                tooltip="Agregar al carrito",
                                on_click=lambda e, item=it, tp=("producto" if is_prod else "servicio"): add_to_cart(item, tp),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=10,
                    bgcolor="#1e293b",
                    border_radius=8,
                    border=_all_border(1, "#334155"),
                )
                self.catalog_container.controls.append(card_item)

            self.page.update()

        def add_to_cart(item: dict, tipo: str):
            item_id = item["id"]
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
                })
            render_cart()
            show_toast(f"'{item['nombre']}' agregado al carrito.")

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
                                ft.Icon(ft.Icons.SHOPPING_BAG_OUTLINED, size=40, color="#64748b"),
                                ft.Text("Carrito de compras vacío", color="#94a3b8", size=13),
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

                tf_desc = ft.TextField(
                    value=f"{desc:.2f}",
                    width=60,
                    height=32,
                    text_size=11,
                    content_padding=ft.Padding.symmetric(horizontal=4, vertical=0),
                    on_change=lambda e, i=idx: update_discount(i, e.control.value),
                )

                row_cart = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(f"{item['codigo']} - {item['nombre']}", size=12, weight=ft.FontWeight.BOLD, color="#f8fafc", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text(f"P.Unit: ${price:.2f} | Total: ${total_i:.2f}", size=11, color="#94a3b8"),
                                ],
                                spacing=1,
                                expand=True,
                            ),
                            ft.Row(
                                controls=[
                                    ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINED, icon_size=18, icon_color="#f87171", on_click=lambda e, i=idx: update_qty(i, -1)),
                                    ft.Text(f"{int(qty) if qty.is_integer() else qty:.1f}", size=12, weight=ft.FontWeight.BOLD),
                                    ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINED, icon_size=18, icon_color="#34d399", on_click=lambda e, i=idx: update_qty(i, 1)),
                                ],
                                spacing=0,
                            ),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE_ROUNDED, icon_size=18, icon_color="#ef4444", on_click=lambda e, i=idx: remove_item(i)),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=8,
                    bgcolor="#1e293b",
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

            tot_final = sub15 + sub0 + iva_t

            txt_sub15.value = f"${sub15:.2f}"
            txt_sub0.value = f"${sub0:.2f}"
            txt_desc.value = f"${total_d:.2f}"
            txt_iva.value = f"${iva_t:.2f}"
            txt_total.value = f"${tot_final:.2f}"

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
                    ft.FilledButton("Guardar", style=ft.ButtonStyle(bgcolor="#2563eb", color="#ffffff"), on_click=save_quick_client),
                ],
            )
            show_dialog(dlg)

        def emit_invoice(e):
            can_write = AppState.has_permission("can_write")
            if not can_write:
                show_toast("No tienes permisos de emisión de facturas.", is_error=True)
                return

            if not self.cart_items:
                show_toast("El carrito está vacío. Agregue productos o servicios.", is_error=True)
                return

            if not self.selected_client_id:
                show_toast("Seleccione un cliente para emitir la factura.", is_error=True)
                return

            success, result = InvoiceController.create_invoice(
                client_id=self.selected_client_id,
                cart_items=self.cart_items,
                forma_pago=dd_payment.value
            )

            if not success:
                show_toast(result, is_error=True)
                return

            secuencial = result.get("secuencial")
            clave_acceso = result.get("clave_acceso")
            pdf_path = result.get("pdf_path")
            xml_path = result.get("xml_path")
            email_status = result.get("email_status", "")

            def open_pdf(ev):
                if pdf_path and os.path.exists(pdf_path):
                    import subprocess
                    subprocess.Popen(["xdg-open", pdf_path])

            def open_xml(ev):
                if xml_path and os.path.exists(xml_path):
                    import subprocess
                    subprocess.Popen(["xdg-open", xml_path])

            def reset_pos(ev):
                close_dialog(dlg)
                self.cart_items = []
                load_initial_data()
                show_toast("Venta completada. POS listo para nueva factura.")

            dlg = ft.AlertDialog(
                title=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINED, color="#34d399", size=28),
                        ft.Text("Factura Emitida Exitosamente", weight=ft.FontWeight.BOLD, color="#34d399"),
                    ],
                    spacing=10,
                ),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(f"Secuencial: {secuencial}", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text(f"Clave Acceso SRI:\n{clave_acceso}", size=11, color="#94a3b8"),
                            ft.Divider(height=1),
                            ft.Text(f"Estado Envíos:\n{email_status}", size=12, color="#60a5fa"),
                        ],
                        tight=True,
                        spacing=10,
                    ),
                    width=450,
                ),
                actions=[
                    ft.OutlinedButton("Abrir XML", icon=ft.Icons.CODE_ROUNDED, on_click=open_xml),
                    ft.FilledButton("Abrir PDF (RIDE)", icon=ft.Icons.PICTURE_IN_PICTURE_ROUNDED, style=ft.ButtonStyle(bgcolor="#2563eb", color="#ffffff"), on_click=open_pdf),
                    ft.FilledButton("Nueva Venta", icon=ft.Icons.ADD_SHOPPING_CART_ROUNDED, style=ft.ButtonStyle(bgcolor="#059669", color="#ffffff"), on_click=reset_pos),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            show_dialog(dlg)

        def set_tab(tab_name: str):
            self.catalog_tab = tab_name
            btn_tab_prod.style = ft.ButtonStyle(bgcolor="#2563eb" if tab_name == "productos" else "#1e293b", color="#ffffff")
            btn_tab_serv.style = ft.ButtonStyle(bgcolor="#2563eb" if tab_name == "servicios" else "#1e293b", color="#ffffff")
            render_catalog()

        btn_tab_prod = ft.FilledButton(
            "Productos",
            icon=ft.Icons.INVENTORY_2_OUTLINED,
            style=ft.ButtonStyle(bgcolor="#2563eb", color="#ffffff"),
            on_click=lambda e: set_tab("productos"),
            expand=True,
            height=38,
        )
        btn_tab_serv = ft.FilledButton(
            "Servicios",
            icon=ft.Icons.HANDYMAN_OUTLINED,
            style=ft.ButtonStyle(bgcolor="#1e293b", color="#ffffff"),
            on_click=lambda e: set_tab("servicios"),
            expand=True,
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
                    ft.Row([btn_tab_prod, btn_tab_serv], spacing=8),
                    search_catalog_tf,
                    self.catalog_container,
                ],
                spacing=10,
                expand=True,
            ),
            padding=12,
            bgcolor="#0f172a",
            border_radius=10,
            border=_all_border(1, "#1e293b"),
            expand=5,
        )

        right_cart_panel = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            dd_client,
                            ft.IconButton(
                                icon=ft.Icons.PERSON_ADD_ROUNDED,
                                icon_color="#3b82f6",
                                tooltip="Nuevo Cliente Rápido",
                                on_click=lambda e: open_quick_client_dialog(),
                            ),
                        ],
                        spacing=4,
                    ),
                    ft.Text("Detalle de la Factura", size=13, weight=ft.FontWeight.BOLD, color="#94a3b8"),
                    self.cart_container,
                    ft.Divider(height=1, color="#334155"),
                    ft.Column(
                        controls=[
                            ft.Row([ft.Text("Subtotal IVA 15%:", size=12, color="#94a3b8"), txt_sub15], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("Subtotal 0%:", size=12, color="#94a3b8"), txt_sub0], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("Total Descuento:", size=12, color="#94a3b8"), txt_desc], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("Monto IVA (15%):", size=12, color="#94a3b8"), txt_iva], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(height=1, color="#334155"),
                            ft.Row([ft.Text("TOTAL A PAGAR:", size=15, weight=ft.FontWeight.BOLD, color="#f8fafc"), txt_total], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ],
                        spacing=4,
                    ),
                    dd_payment,
                    ft.FilledButton(
                        "EMITIR FACTURA ELECTRÓNICA",
                        icon=ft.Icons.POINT_OF_SALE_ROUNDED,
                        style=ft.ButtonStyle(bgcolor="#059669", color="#ffffff"),
                        height=46,
                        on_click=emit_invoice,
                    ),
                ],
                spacing=10,
                expand=True,
            ),
            padding=12,
            bgcolor="#0f172a",
            border_radius=10,
            border=_all_border(1, "#1e293b"),
            expand=4,
        )

        main_row = ft.Row(
            controls=[left_catalog_panel, right_cart_panel],
            spacing=12,
            expand=True,
        )

        load_initial_data()
        return MainLayout(page=self.page, content=main_row, router=self.router)
