import os
from datetime import date
import flet as ft
from core import theme as T
from app.views.layouts.main_layout import MainLayout
from app.controllers.quotation_controller import QuotationController
from app.controllers.client_controller import ClientController
from app.controllers.product_controller import ProductController
from app.controllers.service_controller import ServiceController
from app.views.components.import_export import build_import_export_bar
from app.views.ui_helpers import (
    is_mobile_page,
    open_path,
    send_whatsapp_document,
    stat_card,
)
from app.services.whatsapp_service import build_quote_message, build_whatsapp_link
from app.services.sri_catalogs import FORMAS_PAGO_OPCIONES
from app.models.company_model import CompanyModel
from core.state import AppState

def _all_border(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)

class QuotationsView:
    def __init__(self, page: ft.Page, router):
        self.page = page
        self.router = router
        self.quotations_list = []
        self.search_query = ""

    def render(self):
        if not AppState.has_permission("can_read", "quotations"):
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

        self.quotations_container = ft.Column(spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)
        stats_row = ft.ResponsiveRow(spacing=10, run_spacing=10)

        def refresh_stats():
            total = len(self.quotations_list)
            monto = sum(float(i.get("importe_total") or 0) for i in self.quotations_list)
            enviadas = sum(1 for i in self.quotations_list if "ENVIADA" in (i.get("estado") or ""))
            hoy = date.today().isoformat()
            vigentes = sum(1 for i in self.quotations_list if (i.get("fecha_validez") or "") >= hoy)
            stats_row.controls = [
                stat_card("Cotizaciones", str(total), ft.Icons.DESCRIPTION_ROUNDED, T.PURPLE_TEXT),
                stat_card("Total cotizado", f"${monto:,.2f}", ft.Icons.ATTACH_MONEY_ROUNDED, T.SUCCESS_TEXT),
                stat_card("Enviadas", str(enviadas), ft.Icons.MARK_EMAIL_READ_ROUNDED, T.CYAN_TEXT),
                stat_card("Vigentes", str(vigentes), ft.Icons.EVENT_AVAILABLE_ROUNDED, T.WARNING),
            ]

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

        def load_data():
            self.quotations_list = QuotationController.get_all()
            refresh_stats()
            render_quotations()

        def open_quote_pdf(quot):
            # Regenera para incluir las imágenes actuales de los productos.
            filepath = QuotationController.ensure_quotation_pdf(quot["id"], force=True)
            if not filepath:
                show_toast("No se pudo generar el PDF de la cotización.", is_error=True)
                return
            open_path(self.page, filepath)

        def send_email_action(quot_id: int):
            if not AppState.has_permission("can_write", "quotations"):
                show_toast("No tienes permisos para enviar cotizaciones.", is_error=True)
                return
            show_toast("Enviando cotización por correo...")
            success, msg = QuotationController.send_quotation_email(quot_id)
            if success:
                show_toast(msg)
                load_data()
            else:
                show_toast(msg, is_error=True)

        def send_whatsapp_action(quot):
            if not AppState.has_permission("can_write", "quotations"):
                show_toast("No tienes permisos para enviar cotizaciones.", is_error=True)
                return
            client = ClientController.get_by_id(quot.get("client_id")) if quot.get("client_id") else None
            phone = (client or {}).get("telefono") or ""
            if not phone:
                show_toast("El cliente no tiene un teléfono registrado para WhatsApp.", is_error=True)
                return

            pdf_path = QuotationController.ensure_quotation_pdf(quot["id"], force=True)
            if not pdf_path:
                show_toast("No se pudo generar el PDF de la cotización.", is_error=True)
                return

            company = CompanyModel.get_info() or {}
            empresa = company.get("razon_social") or "Nuestra empresa"
            full = QuotationController.get_by_id(quot["id"]) or {}
            items = full.get("items") or []
            message = build_quote_message(full or quot, items, empresa)
            link = build_whatsapp_link(phone, message)

            def mark_sent():
                QuotationController.mark_whatsapp_sent(quot["id"])
                load_data()

            send_whatsapp_document(
                self.page,
                link=link,
                pdf_path=pdf_path,
                message=message,
                on_sent=mark_sent,
            )

        def invoice_quotation_action(quot):
            full = QuotationController.get_by_id(quot["id"])
            if not full:
                show_toast("Cotización no encontrada.", is_error=True)
                return

            if full.get("invoice_id") or (full.get("estado") or "").upper() == "FACTURADA":
                show_toast("Esta cotización ya fue facturada.", is_error=True)
                return

            if not AppState.has_permission("can_write", "quotations"):
                show_toast("No tienes permisos para facturar cotizaciones.", is_error=True)
                return

            dd_payment = ft.Dropdown(
                label="Forma de pago",
                value="EFECTIVO",
                options=[
                    ft.dropdown.Option(value, label)
                    for value, label in FORMAS_PAGO_OPCIONES
                ],
                width=280,
            )
            sw_send_email = ft.Switch(
                label="Enviar la factura por correo cuando el SRI la autorice",
                value=False,
            )

            def do_invoice(e):
                close_dialog(dlg)
                show_toast("Generando factura...")
                success, result = QuotationController.invoice_quotation(
                    full["id"],
                    forma_pago=dd_payment.value,
                    send_email=bool(sw_send_email.value),
                )
                if success:
                    message = f"Factura {result.get('secuencial')} generada correctamente."
                    if result.get("quotation_warning"):
                        message += f" {result['quotation_warning']}"
                    if sw_send_email.value:
                        message += f" Correo: {result.get('email_status', '')}"
                    show_toast(message)
                    load_data()
                else:
                    show_toast(str(result), is_error=True)

            dlg = ft.AlertDialog(
                title=ft.Text(
                    f"Facturar cotización N° {full.get('secuencial', '')}",
                    weight=ft.FontWeight.BOLD,
                ),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                f"Cliente: {full.get('client_nombre', '')}",
                                size=13,
                                color=T.TEXT,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text("Total a facturar:", size=13, color=T.TEXT_MUTED),
                                    ft.Text(
                                        f"${float(full.get('importe_total') or 0):,.2f}",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=T.SUCCESS_TEXT,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Divider(height=1),
                            dd_payment,
                            sw_send_email,
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.INFO_OUTLINE_ROUNDED,
                                            color=T.WARNING,
                                            size=18,
                                        ),
                                        ft.Text(
                                            "Se generará una factura nueva. Los productos "
                                            "descontarán stock y la cotización quedará "
                                            "marcada como FACTURADA.",
                                            size=11,
                                            color=T.TEXT_MUTED,
                                            expand=True,
                                        ),
                                    ],
                                    spacing=8,
                                    vertical_alignment=ft.CrossAxisAlignment.START,
                                ),
                                bgcolor=T.WARNING_BG,
                                border_radius=8,
                                padding=10,
                            ),
                        ],
                        tight=True,
                        spacing=12,
                    ),
                    width=400,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg)),
                    ft.FilledButton(
                        "Facturar",
                        icon=ft.Icons.RECEIPT_LONG_ROUNDED,
                        style=ft.ButtonStyle(bgcolor=T.SUCCESS, color=T.ON_ACCENT),
                        on_click=do_invoice,
                    ),
                ],
            )
            show_dialog(dlg)

        def delete_quotation_action(quot_id: int):
            if not AppState.has_permission("can_delete", "quotations"):
                show_toast("No tienes permisos para eliminar cotizaciones.", is_error=True)
                return
            dlg_confirm = ft.AlertDialog(
                title=ft.Text("¿Eliminar cotización?", weight=ft.FontWeight.BOLD),
                content=ft.Text("Esta acción no se puede deshacer. ¿Desea continuar?"),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg_confirm)),
                    ft.FilledButton(
                        "Eliminar",
                        style=ft.ButtonStyle(bgcolor=T.DANGER, color=T.ON_ACCENT),
                        on_click=lambda e: do_delete(quot_id, dlg_confirm),
                    ),
                ],
            )
            show_dialog(dlg_confirm)

        def do_delete(quot_id, dlg):
            close_dialog(dlg)
            success, msg = QuotationController.delete(quot_id)
            if success:
                show_toast(msg)
                load_data()
            else:
                show_toast(msg, is_error=True)

        def open_details_dialog(quot):
            quot_full = QuotationController.get_by_id(quot["id"])
            items = quot_full.get("items", []) if quot_full else []

            items_table_rows = []
            for item in items:
                items_table_rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(item.get("codigo", ""), size=12)),
                            ft.DataCell(ft.Text(item.get("descripcion", ""), size=12)),
                            ft.DataCell(ft.Text(f"{float(item.get('cantidad', 1)):.2f}", size=12)),
                            ft.DataCell(ft.Text(f"${float(item.get('precio_unitario', 0)):.2f}", size=12)),
                            ft.DataCell(ft.Text(f"${float(item.get('subtotal', 0)):.2f}", size=12)),
                        ]
                    )
                )

            details_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("CÓDIGO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                    ft.DataColumn(ft.Text("DESCRIPCIÓN", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                    ft.DataColumn(ft.Text("CANTIDAD", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                    ft.DataColumn(ft.Text("PRECIO UNIT", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                    ft.DataColumn(ft.Text("SUBTOTAL", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                ],
                rows=items_table_rows,
                column_spacing=15,
            )

            notas_text = quot.get("notas", "")
            notas_section = []
            if notas_text:
                notas_section = [
                    ft.Divider(height=1),
                    ft.Text("Notas:", weight=ft.FontWeight.BOLD, size=12, color=T.TEXT_MUTED),
                    ft.Text(notas_text, size=12, color=T.TEXT),
                ]

            details_actions = [
                ft.OutlinedButton("Cerrar", on_click=lambda e: close_dialog(dlg)),
            ]
            already_invoiced = bool(quot.get("invoice_id")) or (
                (quot.get("estado") or "").upper() == "FACTURADA"
            )
            if AppState.has_permission("can_write", "quotations") and not already_invoiced:
                details_actions.insert(
                    0,
                    ft.FilledButton(
                        "Facturar",
                        icon=ft.Icons.RECEIPT_LONG_ROUNDED,
                        style=ft.ButtonStyle(bgcolor=T.SUCCESS, color=T.ON_ACCENT),
                        on_click=lambda e: (
                            close_dialog(dlg),
                            invoice_quotation_action(quot),
                        ),
                    ),
                )

            dlg = ft.AlertDialog(
                title=ft.Text(f"Cotización N° {quot['secuencial']}", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(f"Cliente: {quot['client_nombre']} ({quot['client_identificacion']})", size=13),
                            ft.Text(f"Fecha Emisión: {quot['fecha_emision']} | Válida hasta: {quot['fecha_validez']}", size=12, color=T.TEXT_MUTED),
                            ft.Divider(height=1),
                            details_table,
                            ft.Divider(height=1),
                            ft.Row(
                                controls=[
                                    ft.Text("TOTAL COTIZACIÓN:", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"${float(quot['importe_total']):.2f}", weight=ft.FontWeight.BOLD, size=16, color=T.SUCCESS_TEXT),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                        ] + notas_section,
                        tight=True,
                        spacing=10,
                    ),
                    width=600,
                ),
                actions=details_actions,
            )
            show_dialog(dlg)

        def render_quotations():
            self.quotations_container.controls.clear()

            filtered = []
            for quot in self.quotations_list:
                q = self.search_query.lower()
                matches = (
                    not q or
                    q in quot["secuencial"].lower() or
                    q in quot["client_nombre"].lower() or
                    q in quot["client_identificacion"].lower()
                )
                if matches:
                    filtered.append(quot)

            if not filtered:
                self.quotations_container.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=48, color=T.ICON_MUTED),
                                ft.Text("No se encontraron cotizaciones", color=T.TEXT_MUTED, size=16),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10
                        ),
                        padding=40,
                        alignment=ft.Alignment(0, 0)
                    )
                )
                self.page.update()
                return

            rows = []
            cards = []
            can_write = AppState.has_permission("can_write", "quotations")
            can_delete = AppState.has_permission("can_delete", "quotations")
            for quot in filtered:
                est = quot.get("estado", "EMITIDA")
                is_sent = "ENVIADA" in est
                is_invoiced = bool(quot.get("invoice_id")) or "FACTURADA" in est
                status_chip = ft.Container(
                    content=ft.Text(
                        est,
                        size=11,
                        color=T.SUCCESS_TEXT if is_invoiced else (T.CYAN_TEXT if is_sent else T.INFO_TEXT),
                        weight=ft.FontWeight.BOLD,
                    ),
                    bgcolor=T.SUCCESS_BG if is_invoiced else T.INFO_BG,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    border_radius=12,
                )

                actions = ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.VISIBILITY_OUTLINED,
                            icon_color=T.CYAN_TEXT,
                            tooltip="Ver detalles de la cotización",
                            on_click=lambda e, q=quot: open_details_dialog(q),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.RECEIPT_LONG_ROUNDED,
                            icon_color=T.SUCCESS_TEXT,
                            tooltip=(
                                "Cotización ya facturada"
                                if is_invoiced
                                else "Facturar cotización"
                            ),
                            on_click=lambda e, q=quot: invoice_quotation_action(q),
                            disabled=is_invoiced or not can_write,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.PICTURE_IN_PICTURE_ROUNDED,
                            icon_color=T.DANGER,
                            tooltip="Ver / Abrir PDF",
                            on_click=lambda e, q=quot: open_quote_pdf(q),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.EMAIL_OUTLINED,
                            icon_color=T.SUCCESS,
                            tooltip="Enviar por correo al cliente",
                            on_click=lambda e, q=quot: send_email_action(q["id"]),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CHAT_OUTLINED,
                            icon_color=T.WHATSAPP,
                            tooltip="Enviar por WhatsApp",
                            on_click=lambda e, q=quot: send_whatsapp_action(q),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                            icon_color=T.DANGER if can_delete else T.TEXT_SUBTLE,
                            tooltip=(
                                "No se puede eliminar una cotización facturada"
                                if is_invoiced
                                else (
                                    "Eliminar cotización"
                                    if can_delete
                                    else "Sin permiso para eliminar"
                                )
                            ),
                            on_click=lambda e, q=quot: delete_quotation_action(q["id"]),
                            disabled=is_invoiced or not can_delete,
                        ),
                    ],
                    spacing=0,
                )

                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(quot["secuencial"], size=12, weight=ft.FontWeight.BOLD, color=T.PURPLE_TEXT)),
                            ft.DataCell(ft.Text(quot["fecha_emision"], size=12)),
                            ft.DataCell(ft.Text(quot["fecha_validez"], size=12, color=T.WARNING)),
                            ft.DataCell(ft.Text(quot["client_nombre"], size=13, weight=ft.FontWeight.W_500)),
                            ft.DataCell(ft.Text(quot["client_identificacion"], size=12)),
                            ft.DataCell(ft.Text(f"${float(quot['importe_total']):.2f}", size=13, weight=ft.FontWeight.BOLD, color=T.SUCCESS_TEXT)),
                            ft.DataCell(status_chip),
                            ft.DataCell(actions),
                        ]
                    )
                )

                cards.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Column(
                                            controls=[
                                                ft.Text(quot["secuencial"], size=14, weight=ft.FontWeight.BOLD, color=T.PURPLE_TEXT),
                                                ft.Text(quot["client_nombre"], size=13, color=T.TEXT),
                                                ft.Text(f'Válida hasta {quot["fecha_validez"]}', size=11, color=T.TEXT_MUTED),
                                            ],
                                            spacing=2,
                                            expand=True,
                                        ),
                                        ft.Column(
                                            controls=[
                                                status_chip,
                                                ft.Text(f"${float(quot['importe_total']):.2f}", size=15, weight=ft.FontWeight.BOLD, color=T.SUCCESS_TEXT),
                                            ],
                                            spacing=6,
                                            horizontal_alignment=ft.CrossAxisAlignment.END,
                                        ),
                                    ],
                                    vertical_alignment=ft.CrossAxisAlignment.START,
                                ),
                                ft.Row([actions], alignment=ft.MainAxisAlignment.END, wrap=True),
                            ],
                            spacing=8,
                        ),
                        padding=14,
                        bgcolor=T.SURFACE,
                        border_radius=10,
                        border=_all_border(1, T.SURFACE_ALT),
                    )
                )

            if is_mobile_page(self.page):
                self.quotations_container.controls.append(
                    ft.Column(controls=cards, spacing=10)
                )
            else:
                data_table = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("N° COTIZACIÓN", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("EMISIÓN", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("VALIDEZ", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("CLIENTE", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("RUC / CÉDULA", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("TOTAL", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("ESTADO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("ACCIONES", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                    ],
                    rows=rows,
                    heading_row_color=T.SURFACE_ALT,
                    horizontal_margin=15,
                    column_spacing=20,
                )

                self.quotations_container.controls.append(
                    ft.Container(
                        content=data_table,
                        bgcolor=T.SURFACE,
                        border_radius=10,
                        border=_all_border(1, T.SURFACE_ALT),
                        padding=10,
                    )
                )
            self.page.update()

        def on_search_change(e):
            self.search_query = e.control.value
            render_quotations()

        search_field = ft.TextField(
            hint_text="Buscar por N° cotización, cliente o RUC...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=on_search_change,
            height=42,
            width=280,
            text_size=14,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=0),
        )

        btn_new = ft.FilledButton(
            "Nueva Cotización",
            icon=ft.Icons.ADD_ROUNDED,
            style=ft.ButtonStyle(bgcolor=T.PURPLE_BTN, color=T.ON_ACCENT),
            height=42,
            on_click=lambda e: self.router.navigate("/quotations/new"),
        )

        import_export_bar = build_import_export_bar(self.page, kind="quotes", on_changed=load_data)

        header_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.DESCRIPTION_ROUNDED, size=28, color=T.PURPLE_TEXT),
                            ft.Column(
                                controls=[
                                    ft.Text("Historial de Cotizaciones", size=20, weight=ft.FontWeight.BOLD, color=T.TEXT),
                                    ft.Text("Gestión de proformas: crear, facturar, enviar por correo/WhatsApp y descargar PDF", size=12, color=T.TEXT_MUTED),
                                ],
                                spacing=0,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Row(
                        controls=[search_field, btn_new, import_export_bar],
                        spacing=10,
                        wrap=True,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=12,
                tight=True,
            ),
            padding=16,
            bgcolor=T.SURFACE,
            border_radius=10,
            border=_all_border(1, T.SURFACE_ALT),
        )

        main_content = ft.Column(
            controls=[
                header_card,
                stats_row,
                ft.Container(height=10),
                self.quotations_container,
            ],
            expand=True,
            spacing=10,
            scroll=ft.ScrollMode.AUTO if is_mobile_page(self.page) else None,
        )

        load_data()
        return MainLayout(page=self.page, content=main_content, router=self.router)
