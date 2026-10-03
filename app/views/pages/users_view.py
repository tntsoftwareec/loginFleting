import flet as ft
from app.views.layouts.main_layout import MainLayout
from app.controllers.user_controller import UserController
from app.controllers.role_controller import RoleController
from core.state import AppState

def _all_border(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)

class UsersView:
    def __init__(self, page: ft.Page, router):
        self.page = page
        self.router = router
        self.users_list = []
        self.roles_list = []
        self.search_query = ""
        self.selected_role_filter = "ALL"
        self.selected_status_filter = "ALL"

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

        self.users_container = ft.Column(spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)

        # Dialog helpers for consistent show/close across Flet versions
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
            self.users_list = UserController.get_all()
            self.roles_list = RoleController.get_all()
            if hasattr(self, "role_filter_dropdown") and self.role_filter_dropdown:
                self.role_filter_dropdown.options = [ft.dropdown.Option("ALL", "Todos los Roles")] + [
                    ft.dropdown.Option(str(r["id"]), r["name"]) for r in self.roles_list
                ]
            render_users()

        def get_role_badge_style(role_name: str):
            r_lower = role_name.lower()
            if "admin" in r_lower:
                return {"bg": "#3730a322", "fg": "#818cf8", "icon": ft.Icons.ADMIN_PANEL_SETTINGS_ROUNDED}
            elif "cajero" in r_lower:
                return {"bg": "#065f4622", "fg": "#34d399", "icon": ft.Icons.POINT_OF_SALE_ROUNDED}
            else:
                return {"bg": "#78350f22", "fg": "#fbbf24", "icon": ft.Icons.PERSON_ROUNDED}

        def render_users():
            self.users_container.controls.clear()

            filtered = []
            for u in self.users_list:
                q = self.search_query.lower()
                matches_text = not q or (q in u["name"].lower() or q in u["email"].lower() or q in u.get("role_name", "").lower())
                
                matches_role = True
                if self.selected_role_filter != "ALL":
                    matches_role = str(u.get("role_id")) == str(self.selected_role_filter)

                matches_status = True
                if self.selected_status_filter != "ALL":
                    matches_status = u.get("status", "active") == self.selected_status_filter

                if matches_text and matches_role and matches_status:
                    filtered.append(u)

            if not filtered:
                self.users_container.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.PERSON_OFF_ROUNDED, color="#64748b", size=48),
                                ft.Text("No se encontraron usuarios", color="#94a3b8", size=16),
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
            for user in filtered:
                u_id = user["id"]
                name = user["name"]
                email = user["email"]
                role_name = user.get("role_name", "Sin Rol")
                status = user.get("status", "active")

                badge_cfg = get_role_badge_style(role_name)

                is_active = status == "active"
                status_chip = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                width=8,
                                height=8,
                                border_radius=4,
                                bgcolor="#10b981" if is_active else "#94a3b8",
                            ),
                            ft.Text("Activo" if is_active else "Inactivo", color="#10b981" if is_active else "#94a3b8", size=12, weight=ft.FontWeight.W_500),
                        ],
                        spacing=6,
                    ),
                    padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                    border_radius=20,
                    bgcolor="#10b98115" if is_active else "#64748b15",
                )

                role_badge = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(badge_cfg["icon"], color=badge_cfg["fg"], size=14),
                            ft.Text(role_name, color=badge_cfg["fg"], size=12, weight=ft.FontWeight.W_600),
                        ],
                        spacing=4,
                    ),
                    padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                    border_radius=20,
                    bgcolor=badge_cfg["bg"],
                )

                initial = name[0].upper() if name else "U"
                avatar = ft.Container(
                    content=ft.Text(initial, color="#ffffff", size=16, weight=ft.FontWeight.BOLD),
                    width=42,
                    height=42,
                    border_radius=21,
                    gradient=ft.LinearGradient(
                        colors=["#6366f1", "#4338ca"],
                        begin=ft.Alignment(-1, -1),
                        end=ft.Alignment(1, 1),
                    ),
                    alignment=ft.Alignment(0, 0),
                )

                user_action_btns = []
                if AppState.has_permission("can_update"):
                    user_action_btns.append(
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            icon_color="#818cf8",
                            tooltip="Editar usuario",
                            on_click=lambda e, u=user: open_user_dialog(u),
                        )
                    )
                if AppState.has_permission("can_delete"):
                    user_action_btns.append(
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                            icon_color="#f87171",
                            tooltip="Eliminar usuario",
                            on_click=lambda e, u=user: confirm_delete_dialog(u),
                        )
                    )

                row_card = ft.Container(
                    content=ft.Row(
                        controls=[
                            avatar,
                            ft.Column(
                                controls=[
                                    ft.Text(name, color="#f8fafc", size=15, weight=ft.FontWeight.BOLD),
                                    ft.Text(email, color="#94a3b8", size=12),
                                ],
                                expand=True,
                                spacing=2,
                            ),
                            role_badge,
                            status_chip,
                            ft.Row(
                                controls=user_action_btns,
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

            self.users_container.controls = rows
            self.page.update()

        # Dialog: Add / Edit User
        def open_user_dialog(user=None):
            is_edit = user is not None
            u_id = user["id"] if is_edit else None

            name_in = ft.TextField(
                label="Nombre Completo",
                value=user["name"] if is_edit else "",
                hint_text="Ej: Juan Pérez",
                prefix_icon=ft.Icons.PERSON_OUTLINED,
                bgcolor="#0f172a",
                border_color="#334155",
                focused_border_color="#6366f1",
                color="#f8fafc",
                label_style=ft.TextStyle(color="#94a3b8"),
                border_radius=10,
            )

            email_in = ft.TextField(
                label="Correo Electrónico",
                value=user["email"] if is_edit else "",
                hint_text="usuario@ejemplo.com",
                prefix_icon=ft.Icons.EMAIL_OUTLINED,
                bgcolor="#0f172a",
                border_color="#334155",
                focused_border_color="#6366f1",
                color="#f8fafc",
                label_style=ft.TextStyle(color="#94a3b8"),
                border_radius=10,
            )

            pass_label = "Nueva Contraseña (dejar vacía para conservar)" if is_edit else "Contraseña"
            pass_in = ft.TextField(
                label=pass_label,
                prefix_icon=ft.Icons.LOCK_OUTLINED,
                password=True,
                can_reveal_password=True,
                bgcolor="#0f172a",
                border_color="#334155",
                focused_border_color="#6366f1",
                color="#f8fafc",
                label_style=ft.TextStyle(color="#94a3b8"),
                border_radius=10,
            )

            role_options = [
                ft.dropdown.Option(key=str(r["id"]), text=r["name"])
                for r in self.roles_list
            ]

            initial_role_key = str(user["role_id"]) if is_edit and user.get("role_id") else (str(self.roles_list[0]["id"]) if self.roles_list else None)

            role_dropdown = ft.Dropdown(
                label="Rol",
                options=role_options,
                value=initial_role_key,
                bgcolor="#0f172a",
                border_color="#334155",
                focused_border_color="#6366f1",
                color="#f8fafc",
                label_style=ft.TextStyle(color="#94a3b8"),
                border_radius=10,
            )

            status_dropdown = ft.Dropdown(
                label="Estado",
                options=[
                    ft.dropdown.Option(key="active", text="Activo"),
                    ft.dropdown.Option(key="inactive", text="Inactivo"),
                ],
                value=user.get("status", "active") if is_edit else "active",
                bgcolor="#0f172a",
                border_color="#334155",
                focused_border_color="#6366f1",
                color="#f8fafc",
                label_style=ft.TextStyle(color="#94a3b8"),
                border_radius=10,
            )

            error_msg = ft.Text("", color="#ef4444", size=12, visible=False)

            def save_user(e):
                error_msg.visible = False
                name_val = name_in.value
                email_val = email_in.value
                pass_val = pass_in.value
                role_val = role_dropdown.value
                status_val = status_dropdown.value

                if not role_val:
                    error_msg.value = "Por favor selecciona un rol."
                    error_msg.visible = True
                    self.page.update()
                    return

                if is_edit:
                    success, res = UserController.update(
                        user_id=u_id,
                        name=name_val,
                        email=email_val,
                        role_id=int(role_val),
                        status=status_val,
                        password=pass_val if pass_val else None,
                    )
                else:
                    success, res = UserController.create(
                        name=name_val,
                        email=email_val,
                        password=pass_val,
                        role_id=int(role_val),
                        status=status_val,
                    )

                if success:
                    close_dialog(dialog)
                    load_data()
                    show_toast("Usuario actualizado exitosamente" if is_edit else "Usuario creado exitosamente")
                else:
                    error_msg.value = str(res)
                    error_msg.visible = True
                    self.page.update()

            dialog = ft.AlertDialog(
                title=ft.Text("Editar Usuario" if is_edit else "Nuevo Usuario", color="#f8fafc", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            name_in,
                            email_in,
                            pass_in,
                            role_dropdown,
                            status_dropdown,
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
                        on_click=save_user,
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
        def confirm_delete_dialog(user):
            u_id = user["id"]
            u_name = user["name"]

            def do_delete(e):
                success, msg = UserController.delete(u_id)
                close_dialog(dialog)
                if success:
                    load_data()
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
                    f"¿Estás seguro de que deseas eliminar al usuario '{u_name}'?\nEsta acción no se puede deshacer.",
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

        # Search and Filters
        def on_search_change(e):
            self.search_query = e.control.value
            render_users()

        def on_role_filter_change(e):
            self.selected_role_filter = e.control.value
            render_users()

        def on_status_filter_change(e):
            self.selected_status_filter = e.control.value
            render_users()

        search_input = ft.TextField(
            hint_text="Buscar usuarios por nombre, correo o rol...",
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

        self.role_filter_dropdown = ft.Dropdown(
            value="ALL",
            options=[ft.dropdown.Option("ALL", "Todos los Roles")],
            bgcolor="#1e293b",
            border_color="#334155",
            focused_border_color="#6366f1",
            color="#f8fafc",
            border_radius=12,
            height=46,
            width=180,
        )
        self.role_filter_dropdown.on_change = on_role_filter_change

        status_filter_dropdown = ft.Dropdown(
            value="ALL",
            options=[
                ft.dropdown.Option("ALL", "Todos los Estados"),
                ft.dropdown.Option("active", "Activos"),
                ft.dropdown.Option("inactive", "Inactivos"),
            ],
            bgcolor="#1e293b",
            border_color="#334155",
            focused_border_color="#6366f1",
            color="#f8fafc",
            border_radius=12,
            height=46,
            width=170,
        )
        status_filter_dropdown.on_change = on_status_filter_change

        new_user_btn = ft.FilledButton(
            "Nuevo Usuario",
            icon=ft.Icons.PERSON_ADD_ROUNDED,
            visible=AppState.has_permission("can_write"),
            style=ft.ButtonStyle(
                bgcolor="#6366f1",
                color="#ffffff",
                padding=16,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            on_click=lambda e: open_user_dialog(),
        )

        header = ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(ft.Icons.SUPERVISED_USER_CIRCLE_ROUNDED, color="#ffffff", size=28),
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
                                ft.Text("Gestión de Usuarios", color="#f8fafc", size=24, weight=ft.FontWeight.BOLD),
                                ft.Text("Administra los usuarios registrados y la asignación de sus roles", color="#64748b", size=13),
                            ],
                            spacing=2,
                        ),
                    ],
                    spacing=14,
                ),
                new_user_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        toolbar = ft.Row(
            controls=[
                search_input,
                self.role_filter_dropdown,
                status_filter_dropdown,
            ],
            spacing=10,
        )

        content_layout = ft.Container(
            content=ft.Column(
                controls=[
                    header,
                    ft.Divider(color="#1e293b", height=24),
                    toolbar,
                    ft.Container(height=8),
                    self.users_container,
                ],
                spacing=12,
                expand=True,
            ),
            padding=24,
            expand=True,
        )

        load_data()

        return MainLayout(
            page=self.page,
            content=content_layout,
            router=self.router,
        )
