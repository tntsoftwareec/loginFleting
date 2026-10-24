import flet as ft
from core import theme as T
from app.views.layouts.main_layout import MainLayout
from app.controllers.supplier_controller import SupplierController
from app.services.excel_service import ExcelService
from app.views.ui_helpers import form_dialog_width, is_mobile_page
from core.state import AppState

# Botones con paleta pastel exclusiva para Proveedores.
PASTEL_TEXT = "#0f172a"
PASTEL_BLUE = "#bfdbfe"
PASTEL_GREEN = "#bbf7d0"
PASTEL_PURPLE = "#ddd6fe"
PASTEL_PINK = "#fbcfe8"
PASTEL_RED = "#fca5a5"
PASTEL_GRAY = "#e5e7eb"

def _all_border(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)

class SuppliersView:
    def __init__(self, page: ft.Page, router):
        self.page = page
        self.router = router
        self.suppliers_list = []
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

        mobile = is_mobile_page(self.page)
        self.suppliers_container = ft.Column(spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)

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
                duration=3000,
            )
            if hasattr(self.page, "show_dialog"):
                self.page.show_dialog(snack)
            else:
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()

        def load_data():
            self.suppliers_list = SupplierController.get_all()
            render_suppliers()

        def render_suppliers():
            self.suppliers_container.controls.clear()

            filtered = []
            for s in self.suppliers_list:
                q = self.search_query.lower()
                matches = (
                    not q or
                    q in s["razon_social"].lower() or
                    q in s["identificacion"].lower() or
                    q in s["email"].lower() or
                    q in (s.get("contacto") or "").lower()
                )
                if matches:
                    filtered.append(s)

            if not filtered:
                self.suppliers_container.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=48, color=T.ICON_MUTED),
                                ft.Text("No se encontraron proveedores", color=T.TEXT_MUTED, size=16),
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
            for s in filtered:
                is_active = s.get("status", "active") == "active"
                status_chip = ft.Container(
                    content=ft.Text(
                        "Activo" if is_active else "Inactivo",
                        size=11,
                        color=T.SUCCESS_TEXT if is_active else T.DANGER_TEXT,
                        weight=ft.FontWeight.BOLD,
                    ),
                    bgcolor=T.SUCCESS_BG if is_active else T.DANGER_BG,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    border_radius=12,
                )

                can_update = AppState.has_permission("can_update")
                can_delete = AppState.has_permission("can_delete")

                actions = ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            icon_color=PASTEL_TEXT if can_update else T.TEXT_SUBTLE,
                            bgcolor=PASTEL_BLUE if can_update else T.MUTED_BG,
                            tooltip="Editar proveedor" if can_update else "Sin permiso",
                            disabled=not can_update,
                            on_click=lambda e, supplier=s: open_supplier_dialog(supplier),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINED,
                            icon_color=PASTEL_TEXT if can_delete else T.TEXT_SUBTLE,
                            bgcolor=PASTEL_PINK if can_delete else T.MUTED_BG,
                            tooltip="Eliminar proveedor" if can_delete else "Sin permiso",
                            disabled=not can_delete,
                            on_click=lambda e, supplier=s: open_delete_dialog(supplier),
                        ),
                    ],
                    spacing=6,
                )

                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(s["tipo_documento"], size=12, weight=ft.FontWeight.BOLD)),
                            ft.DataCell(ft.Text(s["identificacion"], size=13)),
                            ft.DataCell(ft.Text(s["razon_social"], size=13, weight=ft.FontWeight.W_500)),
                            ft.DataCell(ft.Text(s.get("contacto") or "-", size=12)),
                            ft.DataCell(ft.Text(s["email"], size=12)),
                            ft.DataCell(ft.Text(s.get("telefono") or "-", size=12)),
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
                                        ft.Container(
                                            content=ft.Icon(
                                                ft.Icons.LOCAL_SHIPPING_ROUNDED,
                                                color=PASTEL_TEXT,
                                                size=20,
                                            ),
                                            width=40,
                                            height=40,
                                            border_radius=10,
                                            bgcolor=PASTEL_BLUE,
                                            alignment=ft.Alignment(0, 0),
                                        ),
                                        ft.Column(
                                            controls=[
                                                ft.Text(
                                                    s["razon_social"],
                                                    size=15,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=T.TEXT,
                                                    max_lines=2,
                                                    overflow=ft.TextOverflow.ELLIPSIS,
                                                ),
                                                ft.Text(
                                                    f'{s["tipo_documento"]} · {s["identificacion"]}',
                                                    size=11,
                                                    color=T.TEXT_MUTED,
                                                ),
                                            ],
                                            spacing=2,
                                            expand=True,
                                        ),
                                        status_chip,
                                    ],
                                    vertical_alignment=ft.CrossAxisAlignment.START,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Row(
                                            controls=[
                                                ft.Icon(ft.Icons.PERSON_OUTLINED, size=14, color=T.TEXT_SUBTLE),
                                                ft.Text(
                                                    s.get("contacto") or "-",
                                                    size=12,
                                                    color=T.TEXT_SECONDARY,
                                                    max_lines=1,
                                                    overflow=ft.TextOverflow.ELLIPSIS,
                                                    expand=True,
                                                ),
                                            ],
                                            spacing=6,
                                        ),
                                        ft.Row(
                                            controls=[
                                                ft.Icon(ft.Icons.EMAIL_OUTLINED, size=14, color=T.TEXT_SUBTLE),
                                                ft.Text(
                                                    s.get("email") or "-",
                                                    size=12,
                                                    color=T.TEXT_SECONDARY,
                                                    max_lines=1,
                                                    overflow=ft.TextOverflow.ELLIPSIS,
                                                    expand=True,
                                                ),
                                            ],
                                            spacing=6,
                                        ),
                                        ft.Row(
                                            controls=[
                                                ft.Icon(ft.Icons.PHONE_OUTLINED, size=14, color=T.TEXT_SUBTLE),
                                                ft.Text(
                                                    s.get("telefono") or "-",
                                                    size=12,
                                                    color=T.TEXT_SECONDARY,
                                                    max_lines=1,
                                                    overflow=ft.TextOverflow.ELLIPSIS,
                                                    expand=True,
                                                ),
                                            ],
                                            spacing=6,
                                        ),
                                        ft.Row(
                                            controls=[
                                                ft.Icon(ft.Icons.LOCATION_ON_OUTLINED, size=14, color=T.TEXT_SUBTLE),
                                                ft.Text(
                                                    s.get("direccion") or "-",
                                                    size=12,
                                                    color=T.TEXT_SECONDARY,
                                                    max_lines=1,
                                                    overflow=ft.TextOverflow.ELLIPSIS,
                                                    expand=True,
                                                ),
                                            ],
                                            spacing=6,
                                        ),
                                    ],
                                    spacing=4,
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

            if mobile:
                self.suppliers_container.controls.append(
                    ft.Column(controls=cards, spacing=10)
                )
            else:
                data_table = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("TIPO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("RUC / IDENT", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("RAZÓN SOCIAL", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("CONTACTO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("EMAIL", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("TELÉFONO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("ESTADO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("ACCIONES", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                    ],
                    rows=rows,
                    heading_row_color=T.SURFACE_ALT,
                    horizontal_margin=15,
                    column_spacing=20,
                )

                self.suppliers_container.controls.append(
                    ft.Container(
                        content=data_table,
                        bgcolor=T.SURFACE,
                        border_radius=10,
                        border=_all_border(1, T.SURFACE_ALT),
                        padding=10,
                    )
                )
            self.page.update()

        def open_supplier_dialog(supplier=None):
            is_edit = supplier is not None
            mobile = is_mobile_page(self.page)
            field_expand = not mobile

            tf_tipo = ft.Dropdown(
                label="Tipo Documento",
                value=supplier["tipo_documento"] if is_edit else "RUC",
                options=[
                    ft.dropdown.Option("RUC", "R.U.C."),
                    ft.dropdown.Option("CEDULA", "Cédula"),
                    ft.dropdown.Option("PASAPORTE", "Pasaporte"),
                ],
                expand=field_expand,
            )

            tf_ident = ft.TextField(
                label="RUC / Identificación",
                value=supplier["identificacion"] if is_edit else "",
                expand=field_expand,
            )
            tf_razon = ft.TextField(
                label="Razón Social / Proveedor",
                value=supplier["razon_social"] if is_edit else "",
                expand=field_expand,
            )
            tf_contact = ft.TextField(
                label="Persona de Contacto",
                value=supplier.get("contacto", "") if is_edit else "",
                expand=field_expand,
            )
            tf_email = ft.TextField(
                label="Correo Electrónico",
                value=supplier["email"] if is_edit else "",
                expand=field_expand,
            )
            tf_tel = ft.TextField(
                label="Teléfono",
                value=supplier.get("telefono", "") if is_edit else "",
                expand=field_expand,
            )
            tf_dir = ft.TextField(
                label="Dirección Matriz / Local",
                value=supplier.get("direccion", "") if is_edit else "",
                multiline=True,
                max_lines=2,
                expand=field_expand,
            )
            sw_status = ft.Switch(
                label="Proveedor Activo",
                value=(supplier.get("status", "active") == "active") if is_edit else True,
            )

            def save_supplier(e):
                tipo = tf_tipo.value
                ident = tf_ident.value
                razon = tf_razon.value
                contact = tf_contact.value
                email = tf_email.value
                tel = tf_tel.value
                direccion = tf_dir.value
                status = "active" if sw_status.value else "inactive"

                if is_edit:
                    success, res = SupplierController.update(
                        supplier["id"], tipo, ident, razon, email, tel, direccion, contact, status
                    )
                else:
                    success, res = SupplierController.create(
                        tipo, ident, razon, email, tel, direccion, contact, status
                    )

                if success:
                    close_dialog(dlg)
                    show_toast("Proveedor guardado exitosamente.")
                    load_data()
                else:
                    show_toast(res, is_error=True)

            if mobile:
                form_controls = [
                    tf_tipo,
                    tf_ident,
                    tf_razon,
                    tf_contact,
                    tf_email,
                    tf_tel,
                    tf_dir,
                    sw_status,
                ]
            else:
                form_controls = [
                    ft.Row([tf_tipo, tf_ident], spacing=10),
                    tf_razon,
                    tf_contact,
                    ft.Row([tf_email, tf_tel], spacing=10),
                    tf_dir,
                    sw_status,
                ]

            dlg = ft.AlertDialog(
                title=ft.Text("Editar Proveedor" if is_edit else "Nuevo Proveedor", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column(
                        controls=form_controls,
                        tight=True,
                        spacing=12,
                    ),
                    width=form_dialog_width(self.page, 500),
                ),
                actions=[
                    ft.TextButton(
                        "Cancelar",
                        on_click=lambda e: close_dialog(dlg),
                        style=ft.ButtonStyle(
                            bgcolor=PASTEL_GRAY,
                            color=PASTEL_TEXT,
                        ),
                    ),
                    ft.FilledButton(
                        "Guardar",
                        bgcolor=PASTEL_GREEN,
                        color=PASTEL_TEXT,
                        on_click=save_supplier,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            show_dialog(dlg)

        def open_delete_dialog(supplier):
            def confirm_delete(e):
                success, msg = SupplierController.delete(supplier["id"])
                close_dialog(dlg)
                if success:
                    show_toast(msg)
                    load_data()
                else:
                    show_toast(msg, is_error=True)

            dlg = ft.AlertDialog(
                title=ft.Text("Confirmar Eliminación", color=T.DANGER, weight=ft.FontWeight.BOLD),
                content=ft.Text(f"¿Estás seguro de eliminar el proveedor '{supplier['razon_social']}'?"),
                actions=[
                    ft.TextButton(
                        "Cancelar",
                        on_click=lambda e: close_dialog(dlg),
                        style=ft.ButtonStyle(
                            bgcolor=PASTEL_GRAY,
                            color=PASTEL_TEXT,
                        ),
                    ),
                    ft.FilledButton(
                        "Eliminar",
                        bgcolor=PASTEL_RED,
                        color=PASTEL_TEXT,
                        on_click=confirm_delete,
                    ),
                ],
            )
            show_dialog(dlg)

        def on_search_change(e):
            self.search_query = e.control.value
            render_suppliers()

        search_field = ft.TextField(
            hint_text="Buscar por nombre, RUC o contacto...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=on_search_change,
            height=42,
            width=260,
            text_size=14,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=0),
        )

        can_write = AppState.has_permission("can_write")
        btn_add = ft.FilledButton(
            "Nuevo Proveedor",
            icon=ft.Icons.ADD,
            bgcolor=PASTEL_GREEN if can_write else PASTEL_GRAY,
            color=PASTEL_TEXT,
            disabled=not can_write,
            on_click=lambda e: open_supplier_dialog(),
            height=42,
        )

        def export_to_excel(e):
            try:
                filepath = ExcelService.export_proveedores(self.suppliers_list)
                show_toast(f"Proveedores exportados a: {filepath}")
            except Exception as ex:
                show_toast(f"Error al exportar: {ex}", is_error=True)

        btn_export = ft.OutlinedButton(
            "Exportar Excel",
            icon=ft.Icons.FILE_DOWNLOAD,
            style=ft.ButtonStyle(
                bgcolor=PASTEL_PURPLE,
                color=PASTEL_TEXT,
                side=ft.BorderSide(1, "#c4b5fd"),
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=export_to_excel,
            height=42,
        )

        header_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(
                                    ft.Icons.LOCAL_SHIPPING_ROUNDED,
                                    size=24,
                                    color=PASTEL_TEXT,
                                ),
                                width=44,
                                height=44,
                                border_radius=10,
                                bgcolor=PASTEL_BLUE,
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        "Gestión de Proveedores",
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        color=T.TEXT,
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        "Directorio de distribuidores y empresas proveedoras",
                                        size=12,
                                        color=T.TEXT_MUTED,
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ],
                                spacing=0,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Row(
                        controls=[search_field, btn_add, btn_export],
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
                ft.Container(height=10),
                self.suppliers_container,
            ],
            expand=True,
            spacing=0,
        )

        load_data()
        return MainLayout(page=self.page, content=main_content, router=self.router)
