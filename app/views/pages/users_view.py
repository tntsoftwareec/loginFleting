import flet as ft
from core import theme as T
from app.views.layouts.main_layout import MainLayout
from app.controllers.user_controller import UserController
from app.controllers.role_controller import RoleController
from app.views.ui_helpers import form_dialog_width, is_mobile_page
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
                        ft.Icon(ft.Icons.LOCK_OUTLINED, color=T.DANGER, size=64),
                        ft.Text("Acceso Restringido", color=T.TEXT, size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("Tu rol actual no posee permisos de lectura (can_read) para acceder a este módulo.", color=T.TEXT_MUTED, size=14, text_align=ft.TextAlign.CENTER),
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
                return {"bg": T.PURPLE_BG, "fg": T.INDIGO_TEXT, "icon": ft.Icons.ADMIN_PANEL_SETTINGS_ROUNDED}
            elif "cajero" in r_lower:
                return {"bg": T.SUCCESS_BG_SOFT, "fg": T.SUCCESS_TEXT, "icon": ft.Icons.POINT_OF_SALE_ROUNDED}
            else:
                return {"bg": T.WARNING_BG_SOFT, "fg": T.WARNING, "icon": ft.Icons.PERSON_ROUNDED}

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
                                ft.Icon(ft.Icons.PERSON_OFF_ROUNDED, color=T.ICON_MUTED, size=48),
                                ft.Text("No se encontraron usuarios", color=T.TEXT_MUTED, size=16),
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
            cards = []
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
                                bgcolor=T.SUCCESS if is_active else T.TEXT_MUTED,
                            ),
                            ft.Text("Activo" if is_active else "Inactivo", color=T.SUCCESS if is_active else T.TEXT_MUTED, size=12, weight=ft.FontWeight.W_500),
                        ],
                        spacing=6,
                    ),
                    padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                    border_radius=20,
                    bgcolor=T.SUCCESS_BG_SOFT if is_active else T.MUTED_BG,
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
                    content=ft.Text(initial, color=T.ON_ACCENT, size=16, weight=ft.FontWeight.BOLD),
                    width=42,
                    height=42,
                    border_radius=21,
                    gradient=ft.LinearGradient(
                        colors=[T.INDIGO, T.INDIGO_DARK],
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
                            icon_color=T.INDIGO_TEXT,
                            tooltip="Editar usuario",
                            on_click=lambda e, u=user: open_user_dialog(u),
                        )
                    )
                if AppState.has_permission("can_delete"):
                    user_action_btns.append(
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                            icon_color=T.DANGER_TEXT,
                            tooltip="Eliminar usuario",
                            on_click=lambda e, u=user: confirm_delete_dialog(u),
                        )
                    )

                if mobile:
                    cards.append(
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            avatar,
                                            ft.Column(
                                                controls=[
                                                    ft.Text(
                                                        name,
                                                        color=T.TEXT,
                                                        size=15,
                                                        weight=ft.FontWeight.BOLD,
                                                        max_lines=2,
                                                        overflow=ft.TextOverflow.ELLIPSIS,
                                                    ),
                                                    ft.Text(
                                                        email,
                                                        color=T.TEXT_MUTED,
                                                        size=12,
                                                        max_lines=1,
                                                        overflow=ft.TextOverflow.ELLIPSIS,
                                                    ),
                                                ],
                                                expand=True,
                                                spacing=2,
                                            ),
                                            ft.Row(
                                                controls=user_action_btns,
                                                spacing=4,
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        vertical_alignment=ft.CrossAxisAlignment.START,
                                    ),
                                    ft.Row(
                                        controls=[role_badge, status_chip],
                                        spacing=8,
                                        wrap=True,
                                    ),
                                ],
                                spacing=10,
                            ),
                            padding=14,
                            border_radius=12,
                            bgcolor=T.SURFACE_ALT,
                            border=_all_border(1, T.BORDER_STRONG),
                        )
                    )
                else:
                    row_card = ft.Container(
                        content=ft.Row(
                            controls=[
                                avatar,
                                ft.Column(
                                    controls=[
                                        ft.Text(name, color=T.TEXT, size=15, weight=ft.FontWeight.BOLD),
                                        ft.Text(email, color=T.TEXT_MUTED, size=12),
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
                        bgcolor=T.SURFACE_ALT,
                        border=_all_border(1, T.BORDER_STRONG),
                    )
                    rows.append(row_card)

            self.users_container.controls = cards if mobile else rows
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
                bgcolor=T.SURFACE,
                border_color=T.BORDER_STRONG,
                focused_border_color=T.INDIGO,
                color=T.TEXT,
                label_style=ft.TextStyle(color=T.TEXT_MUTED),
                border_radius=10,
            )

            email_in = ft.TextField(
                label="Correo Electrónico",
                value=user["email"] if is_edit else "",
                hint_text="usuario@ejemplo.com",
                prefix_icon=ft.Icons.EMAIL_OUTLINED,
                bgcolor=T.SURFACE,
                border_color=T.BORDER_STRONG,
                focused_border_color=T.INDIGO,
                color=T.TEXT,
                label_style=ft.TextStyle(color=T.TEXT_MUTED),
                border_radius=10,
            )

            pass_label = "Nueva Contraseña (dejar vacía para conservar)" if is_edit else "Contraseña"
            pass_in = ft.TextField(
                label=pass_label,
                prefix_icon=ft.Icons.LOCK_OUTLINED,
                password=True,
                can_reveal_password=True,
                bgcolor=T.SURFACE,
                border_color=T.BORDER_STRONG,
                focused_border_color=T.INDIGO,
                color=T.TEXT,
                label_style=ft.TextStyle(color=T.TEXT_MUTED),
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
                bgcolor=T.SURFACE,
                border_color=T.BORDER_STRONG,
                focused_border_color=T.INDIGO,
                color=T.TEXT,
                label_style=ft.TextStyle(color=T.TEXT_MUTED),
                border_radius=10,
            )

            status_dropdown = ft.Dropdown(
                label="Estado",
                options=[
                    ft.dropdown.Option(key="active", text="Activo"),
                    ft.dropdown.Option(key="inactive", text="Inactivo"),
                ],
                value=user.get("status", "active") if is_edit else "active",
                bgcolor=T.SURFACE,
                border_color=T.BORDER_STRONG,
                focused_border_color=T.INDIGO,
                color=T.TEXT,
                label_style=ft.TextStyle(color=T.TEXT_MUTED),
                border_radius=10,
            )

            error_msg = ft.Text("", color=T.DANGER, size=12, visible=False)

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
                title=ft.Text("Editar Usuario" if is_edit else "Nuevo Usuario", color=T.TEXT, weight=ft.FontWeight.BOLD),
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
                    width=form_dialog_width(self.page, 420),
                ),
                actions=[
                    ft.TextButton(
                        "Cancelar",
                        on_click=lambda e: close_dialog(dialog),
                        style=ft.ButtonStyle(color=T.TEXT_MUTED),
                    ),
                    ft.FilledButton(
                        "Guardar",
                        on_click=save_user,
                        style=ft.ButtonStyle(
                            bgcolor=T.INDIGO,
                            color=T.ON_ACCENT,
                        ),
                    ),
                ],
                bgcolor=T.SURFACE,
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
                        ft.Icon(ft.Icons.WARNING_ROUNDED, color=T.AMBER, size=28),
                        ft.Text("Confirmar eliminación", color=T.TEXT, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=10,
                ),
                content=ft.Text(
                    f"¿Estás seguro de que deseas eliminar al usuario '{u_name}'?\nEsta acción no se puede deshacer.",
                    color=T.TEXT_SECONDARY,
                    size=14,
                ),
                actions=[
                    ft.TextButton(
                        "Cancelar",
                        on_click=lambda e: close_dialog(dialog),
                        style=ft.ButtonStyle(color=T.TEXT_MUTED),
                    ),
                    ft.FilledButton(
                        "Eliminar",
                        on_click=do_delete,
                        style=ft.ButtonStyle(
                            bgcolor=T.DANGER,
                            color=T.ON_ACCENT,
                        ),
                    ),
                ],
                bgcolor=T.SURFACE,
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
            bgcolor=T.SURFACE_ALT,
            border_color=T.BORDER_STRONG,
            focused_border_color=T.INDIGO,
            color=T.TEXT,
            border_radius=12,
            height=46,
            expand=True,
            on_change=on_search_change,
        )

        self.role_filter_dropdown = ft.Dropdown(
            value="ALL",
            options=[ft.dropdown.Option("ALL", "Todos los Roles")],
            bgcolor=T.SURFACE_ALT,
            border_color=T.BORDER_STRONG,
            focused_border_color=T.INDIGO,
            color=T.TEXT,
            border_radius=12,
            height=46,
            width=None if mobile else 180,
            expand=mobile,
        )
        self.role_filter_dropdown.on_change = on_role_filter_change

        status_filter_dropdown = ft.Dropdown(
            value="ALL",
            options=[
                ft.dropdown.Option("ALL", "Todos los Estados"),
                ft.dropdown.Option("active", "Activos"),
                ft.dropdown.Option("inactive", "Inactivos"),
            ],
            bgcolor=T.SURFACE_ALT,
            border_color=T.BORDER_STRONG,
            focused_border_color=T.INDIGO,
            color=T.TEXT,
            border_radius=12,
            height=46,
            width=None if mobile else 170,
            expand=mobile,
        )
        status_filter_dropdown.on_change = on_status_filter_change

        new_user_btn = ft.FilledButton(
            "Nuevo Usuario",
            icon=ft.Icons.PERSON_ADD_ROUNDED,
            visible=AppState.has_permission("can_write"),
            style=ft.ButtonStyle(
                bgcolor=T.INDIGO,
                color=T.ON_ACCENT,
                padding=16,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            on_click=lambda e: open_user_dialog(),
        )

        header = ft.ResponsiveRow(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(ft.Icons.SUPERVISED_USER_CIRCLE_ROUNDED, color=T.ON_ACCENT, size=28),
                                width=52,
                                height=52,
                                border_radius=14,
                                gradient=ft.LinearGradient(
                                    colors=[T.INDIGO, T.INDIGO_DARK],
                                    begin=ft.Alignment(-1, -1),
                                    end=ft.Alignment(1, 1),
                                ),
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        "Gestión de Usuarios",
                                        color=T.TEXT,
                                        size=24,
                                        weight=ft.FontWeight.BOLD,
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        "Administra los usuarios registrados y la asignación de sus roles",
                                        color=T.TEXT_SUBTLE,
                                        size=13,
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=14,
                    ),
                    col={"xs": 12, "md": 8},
                ),
                ft.Container(
                    content=ft.Row(
                        controls=[new_user_btn],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    col={"xs": 12, "md": 4},
                ),
            ],
            spacing=12,
            run_spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        if mobile:
            toolbar = ft.Column(
                controls=[
                    ft.Row([search_input], spacing=0),
                    ft.Row([self.role_filter_dropdown, status_filter_dropdown], spacing=10),
                ],
                spacing=10,
            )
        else:
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
                    ft.Divider(color=T.SURFACE_ALT, height=24),
                    toolbar,
                    ft.Container(height=8),
                    self.users_container,
                ],
                spacing=12,
                expand=True,
            ),
            padding=12 if mobile else 24,
            expand=True,
        )

        load_data()

        return MainLayout(
            page=self.page,
            content=content_layout,
            router=self.router,
        )
