import flet as ft
from app.views.layouts.main_layout import MainLayout
from app.controllers.role_controller import RoleController
from core.state import AppState

def _all_border(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)

class RolesView:
    def __init__(self, page: ft.Page, router):
        self.page = page
        self.router = router
        self.roles_list = []
        self.filter_query = ""

    def render(self):
        if not AppState.has_permission("can_read"):
            content_layout = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.LOCK_OUTLINED, color="#ef4444", size=64),
                        ft.Text("Acceso Restringido", color="#f8fafc", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("Tu rol actual no posee permisos de lectura (can_read) para acceder a este módulo.", color="#94a3b8", size=14, text_align=ft.TextAlign.CENTER),
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

        self.roles_container = ft.Column(spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)

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

        def load_roles():
            self.roles_list = RoleController.get_all()
            render_roles()

        def make_perm_chip(label: str, is_active: bool, active_color: str, icon_name: str):
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(icon_name, color=active_color if is_active else "#64748b", size=12),
                        ft.Text(label, color=active_color if is_active else "#64748b", size=11, weight=ft.FontWeight.W_500),
                    ],
                    spacing=3,
                ),
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                border_radius=12,
                bgcolor=f"{active_color}18" if is_active else "#1e293b",
                border=_all_border(1, f"{active_color}44" if is_active else "#334155"),
            )

        def render_roles():
            self.roles_container.controls.clear()
            filtered = [
                r for r in self.roles_list
                if self.filter_query.lower() in r["name"].lower()
                or self.filter_query.lower() in (r.get("description") or "").lower()
            ]

            if not filtered:
                self.roles_container.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.SHIELD_OUTLINED, color="#64748b", size=48),
                                ft.Text("No se encontraron roles", color="#94a3b8", size=16),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        padding=40,
                        alignment=ft.Alignment(0, 0),
                    )
                )
                self.page.update()
                return

            rows = []
            for role in filtered:
                role_id = role["id"]
                name = role["name"]
                description = role.get("description") or "Sin descripción"
                users_count = role.get("users_count", 0)

                can_read = bool(role.get("can_read", 1))
                can_write = bool(role.get("can_write", 1))
                can_update = bool(role.get("can_update", 1))
                can_delete = bool(role.get("can_delete", 1))

                perms_row = ft.Row(
                    controls=[
                        make_perm_chip("Leer", can_read, "#10b981", ft.Icons.VISIBILITY_ROUNDED),
                        make_perm_chip("Escribir", can_write, "#6366f1", ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED),
                        make_perm_chip("Actualizar", can_update, "#f59e0b", ft.Icons.EDIT_ROUNDED),
                        make_perm_chip("Eliminar", can_delete, "#ef4444", ft.Icons.DELETE_FOREVER_ROUNDED),
                    ],
                    spacing=6,
                )

                role_action_btns = []
                if AppState.has_permission("can_update"):
                    role_action_btns.append(
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            icon_color="#818cf8",
                            tooltip="Editar rol y permisos",
                            on_click=lambda e, r=role: open_role_dialog(r),
                        )
                    )
                if AppState.has_permission("can_delete"):
                    role_action_btns.append(
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                            icon_color="#f87171",
                            tooltip="Eliminar rol",
                            on_click=lambda e, r=role: confirm_delete_dialog(r),
                        )
                    )

                row_card = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(ft.Icons.VERIFIED_USER_ROUNDED, color="#6366f1", size=24),
                                width=42,
                                height=42,
                                border_radius=10,
                                bgcolor="#1e1b4b",
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(name, color="#f8fafc", size=15, weight=ft.FontWeight.BOLD),
                                            ft.Container(
                                                content=ft.Row(
                                                    controls=[
                                                        ft.Icon(ft.Icons.PEOPLE_OUTLINED, color="#38bdf8", size=13),
                                                        ft.Text(f"{users_count} usuarios", color="#38bdf8", size=11, weight=ft.FontWeight.W_500),
                                                    ],
                                                    spacing=3,
                                                ),
                                                padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                                border_radius=12,
                                                bgcolor="#0284c722",
                                            ),
                                        ],
                                        spacing=8,
                                    ),
                                    ft.Text(description, color="#94a3b8", size=12, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Container(height=4),
                                    perms_row,
                                ],
                                expand=True,
                                spacing=2,
                            ),
                            ft.Row(
                                controls=role_action_btns,
                                spacing=4,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=14,
                    border_radius=12,
                    bgcolor="#1e293b",
                    border=_all_border(1, "#334155"),
                )
                rows.append(row_card)

            self.roles_container.controls = rows
            self.page.update()

        # Dialogs: Create/Edit Role with Permissions
        def open_role_dialog(role=None):
            is_edit = role is not None
            role_id = role["id"] if is_edit else None

            name_input = ft.TextField(
                label="Nombre del Rol",
                value=role["name"] if is_edit else "",
                hint_text="Ej: Supervisor, Vendedor...",
                bgcolor="#0f172a",
                border_color="#334155",
                focused_border_color="#6366f1",
                color="#f8fafc",
                label_style=ft.TextStyle(color="#94a3b8"),
                border_radius=10,
            )

            desc_input = ft.TextField(
                label="Descripción",
                value=role.get("description", "") if is_edit else "",
                hint_text="Descripción de funciones o permisos del rol...",
                multiline=True,
                min_lines=2,
                max_lines=2,
                bgcolor="#0f172a",
                border_color="#334155",
                focused_border_color="#6366f1",
                color="#f8fafc",
                label_style=ft.TextStyle(color="#94a3b8"),
                border_radius=10,
            )

            # Permission Checkboxes
            can_read_check = ft.Checkbox(
                label="Leer / Visualizar (can_read)",
                value=bool(role.get("can_read", 1)) if is_edit else True,
                fill_color="#10b981",
            )
            can_write_check = ft.Checkbox(
                label="Escribir / Crear (can_write)",
                value=bool(role.get("can_write", 1)) if is_edit else True,
                fill_color="#6366f1",
            )
            can_update_check = ft.Checkbox(
                label="Actualizar / Modificar (can_update)",
                value=bool(role.get("can_update", 1)) if is_edit else True,
                fill_color="#f59e0b",
            )
            can_delete_check = ft.Checkbox(
                label="Eliminar Registros (can_delete)",
                value=bool(role.get("can_delete", 1)) if is_edit else False,
                fill_color="#ef4444",
            )

            permissions_box = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Permisos asignados al rol:", color="#cbd5e1", size=13, weight=ft.FontWeight.BOLD),
                        can_read_check,
                        can_write_check,
                        can_update_check,
                        can_delete_check,
                    ],
                    spacing=4,
                ),
                padding=12,
                border_radius=10,
                bgcolor="#0f172a",
                border=_all_border(1, "#334155"),
            )

            error_msg = ft.Text("", color="#ef4444", size=12, visible=False)

            def save_role(e):
                error_msg.visible = False
                name_val = name_input.value
                desc_val = desc_input.value
                cr = 1 if can_read_check.value else 0
                cw = 1 if can_write_check.value else 0
                cu = 1 if can_update_check.value else 0
                cd = 1 if can_delete_check.value else 0

                if is_edit:
                    success, res = RoleController.update(
                        role_id=role_id,
                        name=name_val,
                        description=desc_val,
                        can_read=cr,
                        can_write=cw,
                        can_update=cu,
                        can_delete=cd,
                    )
                else:
                    success, res = RoleController.create(
                        name=name_val,
                        description=desc_val,
                        can_read=cr,
                        can_write=cw,
                        can_update=cu,
                        can_delete=cd,
                    )

                if success:
                    close_dialog(dialog)
                    load_roles()
                    show_toast("Rol actualizado exitosamente" if is_edit else "Rol creado exitosamente")
                else:
                    error_msg.value = str(res)
                    error_msg.visible = True
                    self.page.update()

            dialog = ft.AlertDialog(
                title=ft.Text("Editar Rol y Permisos" if is_edit else "Nuevo Rol", color="#f8fafc", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            name_input,
                            desc_input,
                            permissions_box,
                            error_msg,
                        ],
                        spacing=12,
                        tight=True,
                    ),
                    width=420,
                ),
                actions=[
                    ft.TextButton(
                        "Cancelar",
                        on_click=lambda e: close_dialog(dialog),
                        style=ft.ButtonStyle(color="#94a3b8"),
                    ),
                    ft.FilledButton(
                        "Guardar",
                        on_click=save_role,
                        style=ft.ButtonStyle(
                            bgcolor="#6366f1",
                            color="#ffffff",
                        ),
                    ),
                ],
                bgcolor="#0f172a",
                shape=ft.RoundedRectangleBorder(radius=16),
            )
            show_dialog(dialog)

        # Dialog: Delete Confirmation
        def confirm_delete_dialog(role):
            role_id = role["id"]
            role_name = role["name"]

            def do_delete(e):
                success, msg = RoleController.delete(role_id)
                close_dialog(dialog)
                if success:
                    load_roles()
                    show_toast(msg)
                else:
                    show_toast(msg, is_error=True)

            dialog = ft.AlertDialog(
                title=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.WARNING_ROUNDED, color="#f59e0b", size=28),
                        ft.Text("Confirmar eliminación", color="#f8fafc", weight=ft.FontWeight.BOLD),
                    ],
                    spacing=10,
                ),
                content=ft.Text(
                    f"¿Estás seguro de que deseas eliminar el rol '{role_name}'?\nEsta acción no se puede deshacer.",
                    color="#cbd5e1",
                    size=14,
                ),
                actions=[
                    ft.TextButton(
                        "Cancelar",
                        on_click=lambda e: close_dialog(dialog),
                        style=ft.ButtonStyle(color="#94a3b8"),
                    ),
                    ft.FilledButton(
                        "Eliminar",
                        on_click=do_delete,
                        style=ft.ButtonStyle(
                            bgcolor="#ef4444",
                            color="#ffffff",
                        ),
                    ),
                ],
                bgcolor="#0f172a",
                shape=ft.RoundedRectangleBorder(radius=16),
            )
            show_dialog(dialog)

        def on_search_change(e):
            self.filter_query = e.control.value
            render_roles()

        search_bar = ft.TextField(
            hint_text="Buscar roles por nombre o descripción...",
            prefix_icon=ft.Icons.SEARCH,
            bgcolor="#1e293b",
            border_color="#334155",
            focused_border_color="#6366f1",
            color="#f8fafc",
            border_radius=12,
            height=46,
            expand=True,
            on_change=on_search_change,
        )

        new_role_btn = ft.FilledButton(
            "Nuevo Rol",
            icon=ft.Icons.ADD_ROUNDED,
            visible=AppState.has_permission("can_write"),
            style=ft.ButtonStyle(
                bgcolor="#6366f1",
                color="#ffffff",
                padding=16,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            on_click=lambda e: open_role_dialog(),
        )

        header = ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS_ROUNDED, color="#ffffff", size=28),
                            width=52,
                            height=52,
                            border_radius=14,
                            gradient=ft.LinearGradient(
                                colors=["#6366f1", "#4f46e5"],
                                begin=ft.Alignment(-1, -1),
                                end=ft.Alignment(1, 1),
                            ),
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Column(
                            controls=[
                                ft.Text("Gestión de Roles y Permisos", color="#f8fafc", size=24, weight=ft.FontWeight.BOLD),
                                ft.Text("Crea roles y asigna permisos de lectura, escritura, actualización y eliminación", color="#64748b", size=13),
                            ],
                            spacing=2,
                        ),
                    ],
                    spacing=14,
                ),
                new_role_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        toolbar = ft.Row(
            controls=[search_bar],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        content_layout = ft.Container(
            content=ft.Column(
                controls=[
                    header,
                    ft.Divider(color="#1e293b", height=24),
                    toolbar,
                    ft.Container(height=8),
                    self.roles_container,
                ],
                spacing=12,
                expand=True,
            ),
            padding=24,
            expand=True,
        )

        load_roles()

        return MainLayout(
            page=self.page,
            content=content_layout,
            router=self.router,
        )
