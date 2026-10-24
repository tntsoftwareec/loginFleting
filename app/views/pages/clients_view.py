import flet as ft
from core import theme as T
from app.views.layouts.main_layout import MainLayout
from app.controllers.client_controller import ClientController
from app.views.components.import_export import build_import_export_bar
from app.views.ui_helpers import is_mobile_page
from core.state import AppState

def _all_border(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)

class ClientsView:
    def __init__(self, page: ft.Page, router):
        self.page = page
        self.router = router
        self.clients_list = []
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

        self.clients_container = ft.Column(spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)

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
            self.clients_list = ClientController.get_all()
            render_clients()

        def render_clients():
            self.clients_container.controls.clear()

            filtered = []
            for c in self.clients_list:
                q = self.search_query.lower()
                matches = (
                    not q or
                    q in c["razon_social"].lower() or
                    q in c["identificacion"].lower() or
                    q in c["email"].lower() or
                    q in (c.get("direccion") or "").lower()
                )
                if matches:
                    filtered.append(c)

            if not filtered:
                self.clients_container.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=48, color=T.ICON_MUTED),
                                ft.Text("No se encontraron clientes", color=T.TEXT_MUTED, size=16),
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
            for c in filtered:
                is_active = c.get("status", "active") == "active"
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
                            icon_color=T.INFO if can_update else T.TEXT_SUBTLE,
                            tooltip="Editar cliente" if can_update else "Sin permiso",
                            disabled=not can_update,
                            on_click=lambda e, client=c: open_client_dialog(client),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINED,
                            icon_color=T.DANGER if can_delete else T.TEXT_SUBTLE,
                            tooltip="Eliminar cliente" if can_delete else "Sin permiso",
                            disabled=not can_delete,
                            on_click=lambda e, client=c: open_delete_dialog(client),
                        ),
                    ],
                    spacing=0,
                )

                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(c["tipo_documento"], size=12, weight=ft.FontWeight.BOLD)),
                            ft.DataCell(ft.Text(c["identificacion"], size=13)),
                            ft.DataCell(ft.Text(c["razon_social"], size=13, weight=ft.FontWeight.W_500)),
                            ft.DataCell(ft.Text(c["email"], size=12)),
                            ft.DataCell(ft.Text(c.get("telefono") or "-", size=12)),
                            ft.DataCell(ft.Text(c.get("direccion") or "-", size=12)),
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
                                                ft.Text(c["razon_social"], size=15, weight=ft.FontWeight.BOLD, color=T.TEXT),
                                                ft.Text(f'{c["tipo_documento"]} · {c["identificacion"]}', size=11, color=T.TEXT_MUTED),
                                            ],
                                            spacing=2,
                                            expand=True,
                                        ),
                                        status_chip,
                                    ],
                                    vertical_alignment=ft.CrossAxisAlignment.START,
                                ),
                                ft.Row([ft.Icon(ft.Icons.EMAIL_OUTLINED, size=14, color=T.TEXT_SUBTLE),
                                        ft.Text(c["email"] or "-", size=12, color=T.TEXT_SECONDARY)], spacing=6),
                                ft.Row([ft.Icon(ft.Icons.PHONE_OUTLINED, size=14, color=T.TEXT_SUBTLE),
                                        ft.Text(c.get("telefono") or "-", size=12, color=T.TEXT_SECONDARY)], spacing=6),
                                ft.Row([ft.Icon(ft.Icons.LOCATION_ON_OUTLINED, size=14, color=T.TEXT_SUBTLE),
                                        ft.Text(c.get("direccion") or "-", size=12, color=T.TEXT_SECONDARY)], spacing=6),
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
                self.clients_container.controls.append(
                    ft.Column(controls=cards, spacing=10)
                )
            else:
                data_table = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("TIPO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("IDENTIFICACIÓN", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("RAZÓN SOCIAL / NOMBRE", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("EMAIL", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("TELÉFONO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("DIRECCIÓN", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("ESTADO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("ACCIONES", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                    ],
                    rows=rows,
                    heading_row_color=T.SURFACE_ALT,
                    horizontal_margin=15,
                    column_spacing=20,
                )

                self.clients_container.controls.append(
                    ft.Container(
                        content=data_table,
                        bgcolor=T.SURFACE,
                        border_radius=10,
                        border=_all_border(1, T.SURFACE_ALT),
                        padding=10,
                    )
                )
            self.page.update()

        # Dialog Create/Edit
        def open_client_dialog(client=None):
            is_edit = client is not None

            tf_tipo = ft.Dropdown(
                label="Tipo Documento",
                value=client["tipo_documento"] if is_edit else "CEDULA",
                options=[
                    ft.dropdown.Option("CEDULA", "Cédula de Identidad"),
                    ft.dropdown.Option("RUC", "R.U.C."),
                    ft.dropdown.Option("PASAPORTE", "Pasaporte"),
                    ft.dropdown.Option("CONSUMIDOR_FINAL", "Consumidor Final"),
                ],
                expand=True,
            )

            tf_ident = ft.TextField(
                label="Identificación / RUC",
                value=client["identificacion"] if is_edit else "",
                expand=True,
            )
            tf_razon = ft.TextField(
                label="Razón Social / Nombre Completo",
                value=client["razon_social"] if is_edit else "",
                expand=True,
            )
            tf_email = ft.TextField(
                label="Correo Electrónico",
                value=client["email"] if is_edit else "",
                expand=True,
            )
            tf_tel = ft.TextField(
                label="Teléfono",
                value=client.get("telefono", "") if is_edit else "",
                expand=True,
            )
            tf_dir = ft.TextField(
                label="Dirección",
                value=client.get("direccion", "") if is_edit else "",
                multiline=True,
                max_lines=2,
                expand=True,
            )
            sw_status = ft.Switch(
                label="Cliente Activo",
                value=(client.get("status", "active") == "active") if is_edit else True,
            )

            def save_client(e):
                tipo = tf_tipo.value
                ident = tf_ident.value
                razon = tf_razon.value
                email = tf_email.value
                tel = tf_tel.value
                direccion = tf_dir.value
                status = "active" if sw_status.value else "inactive"

                if is_edit:
                    success, res = ClientController.update(
                        client["id"], tipo, ident, razon, email, tel, direccion, status
                    )
                else:
                    success, res = ClientController.create(
                        tipo, ident, razon, email, tel, direccion, status
                    )

                if success:
                    close_dialog(dlg)
                    show_toast("Cliente guardado exitosamente.")
                    load_data()
                else:
                    show_toast(res, is_error=True)

            dlg = ft.AlertDialog(
                title=ft.Text("Editar Cliente" if is_edit else "Nuevo Cliente", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row([tf_tipo, tf_ident], spacing=10),
                            tf_razon,
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
                        bgcolor=T.PRIMARY,
                        color=T.ON_ACCENT,
                        on_click=save_client,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            show_dialog(dlg)

        def open_delete_dialog(client):
            def confirm_delete(e):
                success, msg = ClientController.delete(client["id"])
                close_dialog(dlg)
                if success:
                    show_toast(msg)
                    load_data()
                else:
                    show_toast(msg, is_error=True)

            dlg = ft.AlertDialog(
                title=ft.Text("Confirmar Eliminación", color=T.DANGER, weight=ft.FontWeight.BOLD),
                content=ft.Text(f"¿Estás seguro de eliminar el cliente '{client['razon_social']}'?"),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg)),
                    ft.FilledButton("Eliminar", bgcolor=T.DANGER, color=T.ON_ACCENT, on_click=confirm_delete),
                ],
            )
            show_dialog(dlg)

        def on_search_change(e):
            self.search_query = e.control.value
            render_clients()

        # Page Header & Controls
        search_field = ft.TextField(
            hint_text="Buscar por nombre, RUC o email...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=on_search_change,
            height=42,
            width=260,
            text_size=14,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=0),
        )

        can_write = AppState.has_permission("can_write")
        btn_add = ft.FilledButton(
            "Nuevo Cliente",
            icon=ft.Icons.ADD,
            bgcolor=T.PRIMARY if can_write else T.DISABLED_BG,
            color=T.ON_ACCENT,
            disabled=not can_write,
            on_click=lambda e: open_client_dialog(),
            height=42,
        )

        import_export_bar = build_import_export_bar(self.page, kind="customers", on_changed=load_data)

        header_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.PEOPLE_ROUNDED, size=28, color=T.INFO),
                            ft.Column(
                                controls=[
                                    ft.Text("Gestión de Clientes", size=20, weight=ft.FontWeight.BOLD, color=T.TEXT),
                                    ft.Text("Administración del directorio de clientes y contactos", size=12, color=T.TEXT_MUTED),
                                ],
                                spacing=0,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Row(
                        controls=[search_field, btn_add, import_export_bar],
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
                self.clients_container,
            ],
            expand=True,
            spacing=0,
        )

        load_data()
        return MainLayout(page=self.page, content=main_content, router=self.router)
