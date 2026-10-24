import flet as ft
from core import theme as T
from app.views.layouts.main_layout import MainLayout
from app.controllers.service_controller import ServiceController
from core.state import AppState

def _all_border(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)

class ServicesView:
    def __init__(self, page: ft.Page, router):
        self.page = page
        self.router = router
        self.services_list = []
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

        self.services_container = ft.Column(spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)

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
            self.services_list = ServiceController.get_all()
            render_services()

        def queue_service(serv: dict, route: str):
            """Abre el POS o una nueva cotización con el servicio ya cargado."""
            if not AppState.has_permission("can_write"):
                show_toast("No tienes permisos para facturar o cotizar.", is_error=True)
                return
            AppState.pending_cart_items = [{
                "id": serv.get("id"),
                "tipo": "servicio",
                "codigo": serv.get("codigo", "SERV"),
                "nombre": serv.get("nombre", "Servicio"),
                "precio": float(serv.get("precio") or 0),
                "cantidad": 1,
                "descuento": 0.0,
                "iva_porcentaje": float(serv.get("iva_porcentaje") or 0),
            }]
            self.router.navigate(route)

        def render_services():
            self.services_container.controls.clear()

            filtered = []
            for s in self.services_list:
                q = self.search_query.lower()
                matches = (
                    not q or
                    q in s["codigo"].lower() or
                    q in s["nombre"].lower() or
                    q in (s.get("categoria") or "").lower()
                )
                if matches:
                    filtered.append(s)

            if not filtered:
                self.services_container.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=48, color=T.ICON_MUTED),
                                ft.Text("No se encontraron servicios", color=T.TEXT_MUTED, size=16),
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
                        color=T.SUCCESS_TEXT if is_active else T.DANGER_TEXT,
                        weight=ft.FontWeight.BOLD,
                    ),
                    bgcolor=T.SUCCESS_BG if is_active else T.DANGER_BG,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    border_radius=12,
                )

                can_write = AppState.has_permission("can_write")
                can_update = AppState.has_permission("can_update")
                can_delete = AppState.has_permission("can_delete")

                actions = ft.Row(
                    controls=[
                        ft.PopupMenuButton(
                            icon=ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED,
                            icon_color=T.SUCCESS_STRONG if can_write else T.TEXT_SUBTLE,
                            tooltip="Facturar o cotizar este servicio" if can_write else "Sin permiso",
                            disabled=not can_write,
                            items=[
                                ft.PopupMenuItem(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(ft.Icons.POINT_OF_SALE_ROUNDED, size=18, color=T.SUCCESS_STRONG),
                                            ft.Text("Facturar este servicio", size=13),
                                        ],
                                        spacing=10,
                                    ),
                                    on_click=lambda e, serv=s: queue_service(serv, "/pos"),
                                ),
                                ft.PopupMenuItem(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(ft.Icons.NOTE_ADD_ROUNDED, size=18, color=T.PURPLE_TEXT),
                                            ft.Text("Cotizar este servicio", size=13),
                                        ],
                                        spacing=10,
                                    ),
                                    on_click=lambda e, serv=s: queue_service(serv, "/quotations/new"),
                                ),
                            ],
                        ),
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            icon_color=T.INFO if can_update else T.TEXT_SUBTLE,
                            tooltip="Editar servicio" if can_update else "Sin permiso",
                            disabled=not can_update,
                            on_click=lambda e, serv=s: open_service_dialog(serv),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINED,
                            icon_color=T.DANGER if can_delete else T.TEXT_SUBTLE,
                            tooltip="Eliminar servicio" if can_delete else "Sin permiso",
                            disabled=not can_delete,
                            on_click=lambda e, serv=s: open_delete_dialog(serv),
                        ),
                    ],
                    spacing=0,
                )

                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(s["codigo"], size=12, weight=ft.FontWeight.BOLD, color=T.CYAN_TEXT)),
                            ft.DataCell(ft.Text(s["nombre"], size=13, weight=ft.FontWeight.W_500)),
                            ft.DataCell(ft.Text(s.get("categoria") or "Servicios", size=12)),
                            ft.DataCell(ft.Text(f"${float(s['precio']):.2f}", size=13, weight=ft.FontWeight.BOLD, color=T.SUCCESS_TEXT)),
                            ft.DataCell(ft.Text(f"{float(s.get('iva_porcentaje', 15.0)):.0f}%", size=12)),
                            ft.DataCell(status_chip),
                            ft.DataCell(actions),
                        ]
                    )
                )

            data_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("CÓDIGO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                    ft.DataColumn(ft.Text("NOMBRE SERVICIO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                    ft.DataColumn(ft.Text("CATEGORÍA", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                    ft.DataColumn(ft.Text("PRECIO TARIFA", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                    ft.DataColumn(ft.Text("IVA", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                    ft.DataColumn(ft.Text("ESTADO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                    ft.DataColumn(ft.Text("ACCIONES", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                ],
                rows=rows,
                heading_row_color=T.SURFACE_ALT,
                horizontal_margin=15,
                column_spacing=20,
            )

            self.services_container.controls.append(
                ft.Container(
                    content=data_table,
                    bgcolor=T.SURFACE,
                    border_radius=10,
                    border=_all_border(1, T.SURFACE_ALT),
                    padding=10,
                )
            )
            self.page.update()

        def open_service_dialog(serv=None):
            is_edit = serv is not None

            tf_cod = ft.TextField(
                label="Código del Servicio",
                value=serv["codigo"] if is_edit else "",
                expand=True,
            )
            tf_nom = ft.TextField(
                label="Nombre del Servicio",
                value=serv["nombre"] if is_edit else "",
                expand=True,
            )
            tf_cat = ft.TextField(
                label="Categoría",
                value=serv.get("categoria", "Servicios") if is_edit else "Servicios",
                expand=True,
            )
            tf_prec = ft.TextField(
                label="Precio del Servicio ($)",
                value=str(serv["precio"]) if is_edit else "0.00",
                expand=True,
            )
            tf_iva = ft.Dropdown(
                label="Tarifa IVA",
                value=str(int(float(serv.get("iva_porcentaje", 15.0)))) if is_edit else "15",
                options=[
                    ft.dropdown.Option("15", "IVA 15%"),
                    ft.dropdown.Option("0", "IVA 0%"),
                ],
                expand=True,
            )
            tf_desc = ft.TextField(
                label="Descripción del Servicio",
                value=serv.get("descripcion", "") if is_edit else "",
                multiline=True,
                max_lines=2,
                expand=True,
            )
            sw_status = ft.Switch(
                label="Servicio Activo",
                value=(serv.get("status", "active") == "active") if is_edit else True,
            )

            def save_service(e):
                cod = tf_cod.value
                nom = tf_nom.value
                cat = tf_cat.value
                precio = tf_prec.value
                iva = tf_iva.value
                desc = tf_desc.value
                status = "active" if sw_status.value else "inactive"

                if is_edit:
                    success, res = ServiceController.update(
                        serv["id"], cod, nom, desc, precio, iva, cat, status
                    )
                else:
                    success, res = ServiceController.create(
                        cod, nom, desc, precio, iva, cat, status
                    )

                if success:
                    close_dialog(dlg)
                    show_toast("Servicio guardado exitosamente.")
                    load_data()
                else:
                    show_toast(res, is_error=True)

            dlg = ft.AlertDialog(
                title=ft.Text("Editar Servicio" if is_edit else "Nuevo Servicio", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row([tf_cod, tf_cat], spacing=10),
                            tf_nom,
                            ft.Row([tf_prec, tf_iva], spacing=10),
                            tf_desc,
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
                        on_click=save_service,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            show_dialog(dlg)

        def open_delete_dialog(serv):
            def confirm_delete(e):
                success, msg = ServiceController.delete(serv["id"])
                close_dialog(dlg)
                if success:
                    show_toast(msg)
                    load_data()
                else:
                    show_toast(msg, is_error=True)

            dlg = ft.AlertDialog(
                title=ft.Text("Confirmar Eliminación", color=T.DANGER, weight=ft.FontWeight.BOLD),
                content=ft.Text(f"¿Estás seguro de eliminar el servicio '{serv['nombre']}'?"),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg)),
                    ft.FilledButton("Eliminar", bgcolor=T.DANGER, color=T.ON_ACCENT, on_click=confirm_delete),
                ],
            )
            show_dialog(dlg)

        def on_search_change(e):
            self.search_query = e.control.value
            render_services()

        search_field = ft.TextField(
            hint_text="Buscar por código, nombre o categoría...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=on_search_change,
            height=42,
            text_size=14,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=0),
            expand=True,
        )

        can_write = AppState.has_permission("can_write")
        btn_add = ft.FilledButton(
            "Nuevo Servicio",
            icon=ft.Icons.ADD,
            bgcolor=T.PRIMARY if can_write else T.DISABLED_BG,
            color=T.ON_ACCENT,
            disabled=not can_write,
            on_click=lambda e: open_service_dialog(),
            height=42,
        )

        header_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.MISCELLANEOUS_SERVICES_ROUNDED, size=28, color=T.CYAN_TEXT),
                            ft.Column(
                                controls=[
                                    ft.Text("Catálogo de Servicios", size=20, weight=ft.FontWeight.BOLD, color=T.TEXT),
                                    ft.Text("Administración de servicios ofrecidos y tarifas de facturación", size=12, color=T.TEXT_MUTED),
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
            bgcolor=T.SURFACE,
            border_radius=10,
            border=_all_border(1, T.SURFACE_ALT),
        )

        main_content = ft.Column(
            controls=[
                header_card,
                ft.Container(height=10),
                self.services_container,
            ],
            expand=True,
            spacing=0,
        )

        load_data()
        return MainLayout(page=self.page, content=main_content, router=self.router)
