import os
import flet as ft
from core import theme as T
from app.views.layouts.main_layout import MainLayout
from app.controllers.invoice_controller import InvoiceController
from app.views.components.import_export import build_import_export_bar
from app.views.ui_helpers import is_mobile_page, open_path, stat_card
from core.state import AppState

def _all_border(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)

class InvoicesView:
    def __init__(self, page: ft.Page, router):
        self.page = page
        self.router = router
        self.invoices_list = []
        self.search_query = ""

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

        self.invoices_container = ft.Column(spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)
        stats_row = ft.ResponsiveRow(spacing=10, run_spacing=10)

        def refresh_stats():
            total = len(self.invoices_list)
            monto = sum(float(i.get("importe_total") or 0) for i in self.invoices_list)
            autorizadas = sum(
                1 for i in self.invoices_list
                if "AUTORIZ" in (i.get("estado") or "").upper()
                and "NO AUTORIZ" not in (i.get("estado") or "").upper()
            )
            stats_row.controls = [
                stat_card("Facturas emitidas", str(total), ft.Icons.RECEIPT_LONG_ROUNDED, T.CYAN_TEXT),
                stat_card("Total facturado", f"${monto:,.2f}", ft.Icons.ATTACH_MONEY_ROUNDED, T.SUCCESS_TEXT),
                stat_card("Autorizadas SRI", str(autorizadas), ft.Icons.VERIFIED_ROUNDED, T.PURPLE),
                stat_card("Pendientes SRI", str(total - autorizadas), ft.Icons.PENDING_ACTIONS_ROUNDED, T.WARNING),
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

        def sri_status_style(estado: str):
            """Devuelve (color_texto, color_fondo) según el estado del SRI."""
            valor = (estado or "GENERADA").upper()
            if any(
                token in valor
                for token in ("DEVUELTA", "NO AUTORIZ", "ERROR", "RECHAZ")
            ):
                return T.DANGER_TEXT, T.DANGER_BG
            if "AUTORIZ" in valor:
                return T.SUCCESS_TEXT, T.SUCCESS_BG
            if "RECIBIDA" in valor or "PROCESO" in valor:
                return T.INFO_TEXT, T.INFO_BG
            return T.WARNING, T.WARNING_BG

        def open_sri_response_dialog(inv, result=None):
            result = result or {}
            estado = result.get("estado") or inv.get("estado") or "GENERADA"
            color, bg = sri_status_style(estado)
            respuesta = (
                result.get("respuesta")
                or inv.get("sri_respuesta")
                or "Sin respuesta registrada."
            )
            numero = result.get("numero_autorizacion") or inv.get("sri_autorizacion") or ""
            fecha = result.get("fecha_autorizacion") or inv.get("sri_fecha_autorizacion") or ""
            ambiente = result.get("ambiente") or ""

            detalles = [
                ft.Row(
                    controls=[
                        ft.Text("Estado:", weight=ft.FontWeight.BOLD, size=12),
                        ft.Container(
                            content=ft.Text(
                                estado,
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=color,
                            ),
                            bgcolor=bg,
                            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                            border_radius=10,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(f"Clave de acceso: {inv.get('clave_acceso', '')}", size=10, color=T.INFO_TEXT),
            ]
            if ambiente:
                detalles.insert(
                    1,
                    ft.Text(f"Ambiente: {ambiente}", size=12, color=T.TEXT_MUTED),
                )
            if numero:
                detalles.append(
                    ft.Text(f"N° Autorización: {numero}", size=11, color=T.TEXT)
                )
            if fecha:
                detalles.append(
                    ft.Text(f"Fecha autorización: {fecha}", size=11, color=T.TEXT)
                )

            dlg = ft.AlertDialog(
                title=ft.Text(
                    f"Respuesta del SRI · Factura {inv.get('secuencial', '')}",
                    weight=ft.FontWeight.BOLD,
                ),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            *detalles,
                            ft.Divider(height=1),
                            ft.Text(
                                "Respuesta del SRI",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=T.TEXT_MUTED,
                            ),
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text(
                                            respuesta,
                                            size=11,
                                            selectable=True,
                                            font_family="monospace",
                                            color=T.TEXT,
                                        ),
                                    ],
                                    scroll=ft.ScrollMode.AUTO,
                                ),
                                height=260,
                                padding=10,
                                bgcolor=T.SURFACE_INSET,
                                border_radius=8,
                                border=_all_border(1, T.SURFACE_ALT),
                                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                            ),
                        ],
                        spacing=8,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    width=680,
                ),
                actions=[
                    ft.OutlinedButton(
                        "Abrir XML",
                        icon=ft.Icons.CODE_ROUNDED,
                        on_click=lambda e: open_file_externally(inv.get("xml_path")),
                    ),
                    ft.FilledButton(
                        "Cerrar",
                        on_click=lambda e: close_dialog(dlg),
                    ),
                ],
            )
            show_dialog(dlg)

        def send_sri_action(inv_id: int):
            show_toast("Firmando y enviando la factura al SRI...")

            def work():
                ok, result = InvoiceController.send_to_sri(inv_id)
                if ok:
                    load_data()
                    inv = next(
                        (i for i in self.invoices_list if i["id"] == inv_id),
                        {},
                    )
                    open_sri_response_dialog(inv, result)
                else:
                    show_toast(str(result), is_error=True)

            self.page.run_thread(work)

        def load_data():
            self.invoices_list = InvoiceController.get_all()
            refresh_stats()
            render_invoices()

        def open_file_externally(filepath: str):
            open_path(self.page, filepath)

        def resend_email_action(inv_id: int):
            show_toast("Re-enviando comprobantes por correo...")
            success, msg = InvoiceController.resend_email(inv_id)
            if success:
                show_toast(msg)
                load_data()
            else:
                show_toast(msg, is_error=True)

        def open_details_dialog(inv):
            inv_full = InvoiceController.get_by_id(inv["id"])
            items = inv_full.get("items", []) if inv_full else []

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

            dlg = ft.AlertDialog(
                title=ft.Text(f"Factura N° {inv['secuencial']}", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(f"Cliente: {inv['client_nombre']} ({inv['client_identificacion']})", size=13),
                            ft.Text(f"Fecha: {inv['fecha_emision']} | Forma Pago: {inv['forma_pago']}", size=12, color=T.TEXT_MUTED),
                            ft.Text(f"Clave de Acceso: {inv['clave_acceso']}", size=10, color=T.INFO_TEXT),
                            ft.Row(
                                controls=[
                                    ft.Text("Estado SRI:", size=12, weight=ft.FontWeight.BOLD),
                                    ft.Container(
                                        content=ft.Text(
                                            (inv.get("estado") or "GENERADA").upper(),
                                            size=11,
                                            weight=ft.FontWeight.BOLD,
                                            color=sri_status_style(inv.get("estado"))[0],
                                        ),
                                        bgcolor=sri_status_style(inv.get("estado"))[1],
                                        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                        border_radius=10,
                                    ),
                                ],
                                spacing=8,
                            ),
                            *(
                                [ft.Text(f"N° Autorización: {inv['sri_autorizacion']}", size=11)]
                                if inv.get("sri_autorizacion") else []
                            ),
                            ft.Text(
                                f"Correo: {(inv.get('email_estado') or 'PENDIENTE').upper()}",
                                size=11,
                                color=T.TEXT_MUTED,
                            ),
                            ft.Divider(height=1),
                            details_table,
                            ft.Divider(height=1),
                            ft.Row(
                                controls=[
                                    ft.Text("TOTAL FACTURA:", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"${float(inv['importe_total']):.2f}", weight=ft.FontWeight.BOLD, size=16, color=T.SUCCESS_TEXT),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                        ],
                        tight=True,
                        spacing=10,
                    ),
                    width=600,
                ),
                actions=[
                    ft.OutlinedButton(
                        "Ver respuesta SRI",
                        icon=ft.Icons.FACT_CHECK_OUTLINED,
                        on_click=lambda e: (
                            close_dialog(dlg),
                            open_sri_response_dialog(inv),
                        ),
                    ),
                    ft.FilledButton(
                        "Enviar al SRI",
                        icon=ft.Icons.CLOUD_UPLOAD_ROUNDED,
                        on_click=lambda e: (close_dialog(dlg), send_sri_action(inv["id"])),
                    ),
                    ft.OutlinedButton("Cerrar", on_click=lambda e: close_dialog(dlg)),
                ],
            )
            show_dialog(dlg)

        def render_invoices():
            self.invoices_container.controls.clear()

            filtered = []
            for inv in self.invoices_list:
                q = self.search_query.lower()
                matches = (
                    not q or
                    q in inv["secuencial"].lower() or
                    q in inv["client_nombre"].lower() or
                    q in inv["client_identificacion"].lower() or
                    q in (inv.get("clave_acceso") or "").lower() or
                    q in (inv.get("sri_autorizacion") or "").lower()
                )
                if matches:
                    filtered.append(inv)

            if not filtered:
                self.invoices_container.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, size=48, color=T.TEXT_SUBTLE),
                                ft.Text("No se encontraron facturas emitidas", color=T.TEXT_MUTED, size=16),
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
            for inv in filtered:
                est = inv.get("estado") or "GENERADA"
                est_color, est_bg = sri_status_style(est)
                status_chip = ft.Container(
                    content=ft.Text(
                        est.upper(),
                        size=11,
                        color=est_color,
                        weight=ft.FontWeight.BOLD,
                    ),
                    bgcolor=est_bg,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    border_radius=12,
                )

                actions = ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.VISIBILITY_OUTLINED,
                            icon_color=T.CYAN_TEXT,
                            tooltip="Ver detalles de la factura",
                            on_click=lambda e, invoice=inv: open_details_dialog(invoice),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.PICTURE_IN_PICTURE_ROUNDED,
                            icon_color=T.DANGER,
                            tooltip="Ver / Abrir PDF (RIDE)",
                            on_click=lambda e, invoice=inv: open_file_externally(invoice.get("pdf_path")),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CODE_ROUNDED,
                            icon_color=T.PURPLE,
                            tooltip="Ver / Abrir XML SRI",
                            on_click=lambda e, invoice=inv: open_file_externally(invoice.get("xml_path")),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLOUD_UPLOAD_ROUNDED,
                            icon_color=T.INFO,
                            tooltip="Enviar al SRI (ambiente configurado en Mi Empresa)",
                            on_click=lambda e, invoice=inv: send_sri_action(invoice["id"]),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SEND_ROUNDED,
                            icon_color=T.SUCCESS,
                            tooltip="Re-enviar por correo al cliente y SRI",
                            on_click=lambda e, invoice=inv: resend_email_action(invoice["id"]),
                        ),
                    ],
                    spacing=0,
                )

                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(inv["secuencial"], size=12, weight=ft.FontWeight.BOLD, color=T.INFO_TEXT)),
                            ft.DataCell(ft.Text(inv["fecha_emision"], size=12)),
                            ft.DataCell(ft.Text(inv["client_nombre"], size=13, weight=ft.FontWeight.W_500)),
                            ft.DataCell(ft.Text(inv["client_identificacion"], size=12)),
                            ft.DataCell(ft.Text(f"${float(inv['importe_total']):.2f}", size=13, weight=ft.FontWeight.BOLD, color=T.SUCCESS_TEXT)),
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
                                                ft.Text(inv["secuencial"], size=14, weight=ft.FontWeight.BOLD, color=T.INFO_TEXT),
                                                ft.Text(inv["client_nombre"], size=13, color=T.TEXT),
                                                ft.Text(f'{inv["client_identificacion"]} · {inv["fecha_emision"]}', size=11, color=T.TEXT_MUTED),
                                            ],
                                            spacing=2,
                                            expand=True,
                                        ),
                                        ft.Column(
                                            controls=[
                                                status_chip,
                                                ft.Text(f"${float(inv['importe_total']):.2f}", size=15, weight=ft.FontWeight.BOLD, color=T.SUCCESS_TEXT),
                                            ],
                                            spacing=6,
                                            horizontal_alignment=ft.CrossAxisAlignment.END,
                                        ),
                                    ],
                                    vertical_alignment=ft.CrossAxisAlignment.START,
                                ),
                                ft.Row([actions], alignment=ft.MainAxisAlignment.END),
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
                self.invoices_container.controls.append(
                    ft.Column(controls=cards, spacing=10)
                )
            else:
                data_table = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("SECUENCIAL", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("FECHA", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
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

                self.invoices_container.controls.append(
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
            render_invoices()

        search_field = ft.TextField(
            hint_text="Buscar por secuencial, cliente o RUC...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=on_search_change,
            height=42,
            width=280,
            text_size=14,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=0),
        )

        import_export_bar = build_import_export_bar(self.page, kind="invoices", on_changed=load_data)

        header_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.RECEIPT_LONG_ROUNDED, size=28, color=T.SUCCESS_STRONG),
                            ft.Column(
                                controls=[
                                    ft.Text("Historial de Facturas Emitidas", size=20, weight=ft.FontWeight.BOLD, color=T.TEXT),
                                    ft.Text("Consulta de comprobantes electrónicos, descargas de RIDE PDF y XML", size=12, color=T.TEXT_MUTED),
                                ],
                                spacing=0,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Row(
                        controls=[search_field, import_export_bar],
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
                self.invoices_container,
            ],
            expand=True,
            spacing=10,
            scroll=ft.ScrollMode.AUTO if is_mobile_page(self.page) else None,
        )

        load_data()
        return MainLayout(page=self.page, content=main_content, router=self.router)
