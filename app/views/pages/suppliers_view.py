import flet as ft
from app.views.layouts.main_layout import MainLayout
from app.controllers.supplier_controller import SupplierController
from core.state import AppState

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
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message, color="#ffffff"),
                bgcolor="#ef4444" if is_error else "#10b981",
                duration=3000
            )
            self.page.snack_bar.open = True
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
                                ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=48, color="#64748b"),
                                ft.Text("No se encontraron proveedores", color="#94a3b8", size=16),
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
            for s in filtered:
                is_active = s.get("status", "active") == "active"
                status_chip = ft.Container(
                    content=ft.Text(
                        "Activo" if is_active else "Inactivo",
                        size=11,
                        color="#34d399" if is_active else "#f87171",
                        weight=ft.FontWeight.BOLD,
                    ),
                    bgcolor="#065f4633" if is_active else "#991b1b33",
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    border_radius=12,
                )

                can_update = AppState.has_permission("can_update")
                can_delete = AppState.has_permission("can_delete")

                actions = ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            icon_color="#3b82f6" if can_update else "#64748b",
                            tooltip="Editar proveedor" if can_update else "Sin permiso",
                            disabled=not can_update,
                            on_click=lambda e, supplier=s: open_supplier_dialog(supplier),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINED,
                            icon_color="#ef4444" if can_delete else "#64748b",
                            tooltip="Eliminar proveedor" if can_delete else "Sin permiso",
                            disabled=not can_delete,
                            on_click=lambda e, supplier=s: open_delete_dialog(supplier),
                        ),
                    ],
                    spacing=0,
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

            data_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("TIPO", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("RUC / IDENT", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("RAZÓN SOCIAL", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("CONTACTO", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("EMAIL", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("TELÉFONO", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("ESTADO", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("ACCIONES", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                ],
                rows=rows,
                heading_row_color="#1e293b",
                horizontal_margin=15,
                column_spacing=20,
            )

            self.suppliers_container.controls.append(
                ft.Container(
                    content=data_table,
                    bgcolor="#0f172a",
                    border_radius=10,
                    border=_all_border(1, "#1e293b"),
                    padding=10,
                )
            )
            self.page.update()

        def open_supplier_dialog(supplier=None):
            is_edit = supplier is not None

            tf_tipo = ft.Dropdown(
                label="Tipo Documento",
                value=supplier["tipo_documento"] if is_edit else "RUC",
                options=[
                    ft.dropdown.Option("RUC", "R.U.C."),
                    ft.dropdown.Option("CEDULA", "Cédula"),
                    ft.dropdown.Option("PASAPORTE", "Pasaporte"),
                ],
                expand=True,
            )

            tf_ident = ft.TextField(
                label="RUC / Identificación",
                value=supplier["identificacion"] if is_edit else "",
                expand=True,
            )
            tf_razon = ft.TextField(
                label="Razón Social / Proveedor",
                value=supplier["razon_social"] if is_edit else "",
                expand=True,
            )
            tf_contact = ft.TextField(
                label="Persona de Contacto",
                value=supplier.get("contacto", "") if is_edit else "",
                expand=True,
            )
            tf_email = ft.TextField(
                label="Correo Electrónico",
                value=supplier["email"] if is_edit else "",
                expand=True,
            )
            tf_tel = ft.TextField(
                label="Teléfono",
                value=supplier.get("telefono", "") if is_edit else "",
                expand=True,
            )
            tf_dir = ft.TextField(
                label="Dirección Matriz / Local",
                value=supplier.get("direccion", "") if is_edit else "",
                multiline=True,
                max_lines=2,
                expand=True,
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

            dlg = ft.AlertDialog(
                title=ft.Text("Editar Proveedor" if is_edit else "Nuevo Proveedor", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row([tf_tipo, tf_ident], spacing=10),
                            tf_razon,
                            tf_contact,
                            ft.Row([tf_email, tf_tel], spacing=10),
                            tf_dir,
                            sw_status,
                        ],
                        tight=True,
                        spacing=12,
                    ),
                    width=500,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg)),
                    ft.FilledButton(
                        "Guardar",
                        bgcolor="#2563eb",
                        color="#ffffff",
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
                title=ft.Text("Confirmar Eliminación", color="#ef4444", weight=ft.FontWeight.BOLD),
                content=ft.Text(f"¿Estás seguro de eliminar el proveedor '{supplier['razon_social']}'?"),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg)),
                    ft.FilledButton("Eliminar", bgcolor="#ef4444", color="#ffffff", on_click=confirm_delete),
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
            text_size=14,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=0),
            expand=True,
        )

        can_write = AppState.has_permission("can_write")
        btn_add = ft.FilledButton(
            "Nuevo Proveedor",
            icon=ft.Icons.ADD,
            bgcolor="#2563eb" if can_write else "#475569",
            color="#ffffff",
            disabled=not can_write,
            on_click=lambda e: open_supplier_dialog(),
            height=42,
        )

        header_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.LOCAL_SHIPPING_ROUNDED, size=28, color="#10b981"),
                            ft.Column(
                                controls=[
                                    ft.Text("Gestión de Proveedores", size=20, weight=ft.FontWeight.BOLD, color="#f8fafc"),
                                    ft.Text("Directorio de distribuidores y empresas proveedoras", size=12, color="#94a3b8"),
                                ],
                                spacing=0,
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Row([search_field, btn_add], spacing=10, width=500),
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
                self.suppliers_container,
            ],
            expand=True,
            spacing=0,
        )

        load_data()
        return MainLayout(page=self.page, content=main_content, router=self.router)
