import os
import subprocess
import flet as ft
from app.views.layouts.main_layout import MainLayout
from app.controllers.invoice_controller import InvoiceController
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

        self.invoices_container = ft.Column(spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)

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

        def load_data():
            self.invoices_list = InvoiceController.get_all()
            render_invoices()

        def open_file_externally(filepath: str):
            if filepath and os.path.exists(filepath):
                try:
                    subprocess.Popen(["xdg-open", filepath])
                except Exception as e:
                    show_toast(f"No se pudo abrir el archivo: {e}", is_error=True)
            else:
                show_toast("El archivo no existe en el disco.", is_error=True)

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
                    ft.DataColumn(ft.Text("CÓDIGO", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("DESCRIPCIÓN", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("CANTIDAD", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("PRECIO UNIT", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("SUBTOTAL", weight=ft.FontWeight.BOLD, color="#94a3b8")),
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
                            ft.Text(f"Fecha: {inv['fecha_emision']} | Forma Pago: {inv['forma_pago']}", size=12, color="#94a3b8"),
                            ft.Text(f"Clave de Acceso: {inv['clave_acceso']}", size=10, color="#60a5fa"),
                            ft.Divider(height=1),
                            details_table,
                            ft.Divider(height=1),
                            ft.Row(
                                controls=[
                                    ft.Text("TOTAL FACTURA:", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"${float(inv['importe_total']):.2f}", weight=ft.FontWeight.BOLD, size=16, color="#34d399"),
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
                    q in (inv.get("clave_acceso") or "").lower()
                )
                if matches:
                    filtered.append(inv)

            if not filtered:
                self.invoices_container.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, size=48, color="#64748b"),
                                ft.Text("No se encontraron facturas emitidas", color="#94a3b8", size=16),
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
            for inv in filtered:
                est = inv.get("estado", "GENERADA")
                is_sent = "ENVIADA" in est
                status_chip = ft.Container(
                    content=ft.Text(
                        "ENVIADA" if is_sent else "GENERADA",
                        size=11,
                        color="#34d399" if is_sent else "#fbbf24",
                        weight=ft.FontWeight.BOLD,
                    ),
                    bgcolor="#065f4633" if is_sent else "#78350f33",
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    border_radius=12,
                )

                actions = ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.VISIBILITY_OUTLINED,
                            icon_color="#38bdf8",
                            tooltip="Ver detalles de la factura",
                            on_click=lambda e, invoice=inv: open_details_dialog(invoice),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.PICTURE_IN_PICTURE_ROUNDED,
                            icon_color="#ef4444",
                            tooltip="Ver / Abrir PDF (RIDE)",
                            on_click=lambda e, invoice=inv: open_file_externally(invoice.get("pdf_path")),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CODE_ROUNDED,
                            icon_color="#a855f7",
                            tooltip="Ver / Abrir XML SRI",
                            on_click=lambda e, invoice=inv: open_file_externally(invoice.get("xml_path")),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SEND_ROUNDED,
                            icon_color="#10b981",
                            tooltip="Re-enviar por correo al cliente y SRI",
                            on_click=lambda e, invoice=inv: resend_email_action(invoice["id"]),
                        ),
                    ],
                    spacing=0,
                )

                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(inv["secuencial"], size=12, weight=ft.FontWeight.BOLD, color="#60a5fa")),
                            ft.DataCell(ft.Text(inv["fecha_emision"], size=12)),
                            ft.DataCell(ft.Text(inv["client_nombre"], size=13, weight=ft.FontWeight.W_500)),
                            ft.DataCell(ft.Text(inv["client_identificacion"], size=12)),
                            ft.DataCell(ft.Text(f"${float(inv['importe_total']):.2f}", size=13, weight=ft.FontWeight.BOLD, color="#34d399")),
                            ft.DataCell(status_chip),
                            ft.DataCell(actions),
                        ]
                    )
                )

            data_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("SECUENCIAL", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("FECHA", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("CLIENTE", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("RUC / CÉDULA", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("TOTAL", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("ESTADO", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("ACCIONES", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                ],
                rows=rows,
                heading_row_color="#1e293b",
                horizontal_margin=15,
                column_spacing=20,
            )

            self.invoices_container.controls.append(
                ft.Container(
                    content=data_table,
                    bgcolor="#0f172a",
                    border_radius=10,
                    border=_all_border(1, "#1e293b"),
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
            text_size=14,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=0),
            expand=True,
        )

        header_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.RECEIPT_LONG_ROUNDED, size=28, color="#059669"),
                            ft.Column(
                                controls=[
                                    ft.Text("Historial de Facturas Emitidas", size=20, weight=ft.FontWeight.BOLD, color="#f8fafc"),
                                    ft.Text("Consulta de comprobantes electrónicos, descargas de RIDE PDF y XML", size=12, color="#94a3b8"),
                                ],
                                spacing=0,
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Container(content=search_field, width=350),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=16,
            bgcolor="#0f172a",
            border_radius=10,
            border=_all_border(1, "#1e293b"),
        )

        main_content = ft.Column(
            controls=[
                header_card,
                ft.Container(height=10),
                self.invoices_container,
            ],
            expand=True,
            spacing=0,
        )

        load_data()
        return MainLayout(page=self.page, content=main_content, router=self.router)
