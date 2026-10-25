import flet as ft
from core import theme as T
from core.permissions import (
    ACTION_COLORS,
    ACTION_LABELS,
    MODULES,
    PRESETS,
    PRESET_ORDER,
    preset_permissions,
)
from core.state import AppState
from app.controllers.role_controller import RoleController
from app.views.layouts.main_layout import MainLayout
from app.views.ui_helpers import is_mobile_page, wide_dialog_width


def _all_border(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)


def _chunk(controls: list, size: int) -> list[list]:
    """Divide controles en filas sin usar ``Row(wrap=True)``.

    Flet 1.0.4 en escritorio pinta un bloque gris cuando un ``Row`` usa
    ``wrap=True`` dentro de un diálogo; por eso armamos las filas a mano.
    """
    size = max(1, int(size))
    return [controls[i:i + size] for i in range(0, len(controls), size)]


class RolesView:
    def __init__(self, page: ft.Page, router):
        self.page = page
        self.router = router
        self.roles_list = []
        self.filter_query = ""

    def render(self):
        if not AppState.has_permission("can_read", "roles"):
            content_layout = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.LOCK_OUTLINED, color=T.DANGER, size=64),
                        ft.Text(
                            "Acceso Restringido",
                            color=T.TEXT,
                            size=22,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            "Tu rol actual no tiene permiso de lectura para el "
                            "módulo de roles y permisos.",
                            color=T.TEXT_MUTED,
                            size=14,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12,
                ),
                padding=60,
                alignment=ft.Alignment(0, 0),
                expand=True,
            )
            return MainLayout(
                page=self.page,
                content=content_layout,
                router=self.router,
            )

        mobile = is_mobile_page(self.page)
        self.roles_container = ft.Column(
            spacing=10,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

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

        def load_roles():
            self.roles_list = RoleController.get_all()
            render_roles()

        def make_module_chip(label: str, icon_name: str):
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            getattr(ft.Icons, icon_name, ft.Icons.APPS),
                            color=T.INDIGO_TEXT,
                            size=12,
                        ),
                        ft.Text(
                            label,
                            color=T.INDIGO_TEXT,
                            size=11,
                            weight=ft.FontWeight.W_500,
                        ),
                    ],
                    spacing=3,
                ),
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                border_radius=12,
                bgcolor=T.INDIGO_BG,
                border=_all_border(1, T.INDIGO),
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
                                ft.Icon(
                                    ft.Icons.SHIELD_OUTLINED,
                                    color=T.ICON_MUTED,
                                    size=48,
                                ),
                                ft.Text(
                                    "No se encontraron roles",
                                    color=T.TEXT_MUTED,
                                    size=16,
                                ),
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
            for role in filtered:
                name = role["name"]
                description = role.get("description") or "Sin descripción"
                users_count = role.get("users_count", 0)
                module_permissions = role.get("module_permissions") or {}

                allowed_modules = [
                    module for module in MODULES
                    if module_permissions.get(module["key"], {}).get("can_read")
                ]

                module_chips = [
                    make_module_chip(module["label"], module["icon"])
                    for module in allowed_modules[:8]
                ]
                if len(allowed_modules) > 8:
                    module_chips.append(
                        make_module_chip(
                            f"+{len(allowed_modules) - 8} más",
                            "MORE_HORIZ",
                        )
                    )
                if not module_chips:
                    module_chips.append(
                        make_module_chip("Sin módulos asignados", "LOCK_OUTLINE")
                    )

                modules_row = ft.Column(
                    controls=[
                        ft.Row(controls=chips, spacing=6)
                        for chips in _chunk(module_chips, 3 if mobile else 8)
                    ],
                    spacing=6,
                )

                role_action_btns = []
                if AppState.has_permission("can_update", "roles"):
                    role_action_btns.append(
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            icon_color=T.INDIGO_TEXT,
                            tooltip="Editar rol y permisos",
                            on_click=lambda e, r=role: open_role_dialog(r),
                        )
                    )
                if AppState.has_permission("can_delete", "roles"):
                    role_action_btns.append(
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                            icon_color=T.DANGER_TEXT,
                            tooltip="Eliminar rol",
                            on_click=lambda e, r=role: confirm_delete_dialog(r),
                        )
                    )

                role_icon = ft.Container(
                    content=ft.Icon(
                        ft.Icons.VERIFIED_USER_ROUNDED,
                        color=T.INDIGO,
                        size=24,
                    ),
                    width=42,
                    height=42,
                    border_radius=10,
                    bgcolor=T.INDIGO_BG,
                    alignment=ft.Alignment(0, 0),
                )

                users_badge = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.PEOPLE_OUTLINED,
                                color=T.CYAN_TEXT,
                                size=13,
                            ),
                            ft.Text(
                                f"{users_count} usuarios",
                                color=T.CYAN_TEXT,
                                size=11,
                                weight=ft.FontWeight.W_500,
                            ),
                        ],
                        spacing=3,
                    ),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                    border_radius=12,
                    bgcolor=T.INFO_BG_SOFT,
                )

                role_info = ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(
                                    name,
                                    color=T.TEXT,
                                    size=15,
                                    weight=ft.FontWeight.BOLD,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    expand=True,
                                ),
                                users_badge,
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Text(
                            description,
                            color=T.TEXT_MUTED,
                            size=12,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                    expand=True,
                    spacing=2,
                )

                top_row = ft.Row(
                    controls=[
                        role_icon,
                        role_info,
                        ft.Row(controls=role_action_btns, spacing=4),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                )

                card = ft.Container(
                    content=ft.Column(
                        controls=[top_row, modules_row],
                        spacing=8,
                    ),
                    padding=14,
                    border_radius=12,
                    bgcolor=T.SURFACE_ALT,
                    border=_all_border(1, T.BORDER_STRONG),
                )
                if mobile:
                    cards.append(card)
                else:
                    rows.append(card)

            self.roles_container.controls = cards if mobile else rows
            self.page.update()

        # ── Diálogo crear/editar rol con matriz de permisos ────────────────
        def open_role_dialog(role=None):
            # El ancho de página puede cambiar después del primer render;
            # recalculamos el layout del diálogo con el tamaño actual.
            dialog_width = wide_dialog_width(self.page, 860)
            dialog_mobile = is_mobile_page(self.page) or dialog_width < 600
            checkbox_width = (
                max(56, min(82, (dialog_width - 42) // 4))
                if dialog_mobile
                else 82
            )
            is_edit = role is not None
            role_id = role["id"] if is_edit else None
            current_permissions = (
                role.get("module_permissions") or {}
                if is_edit
                else {}
            )

            name_input = ft.TextField(
                label="Nombre del Rol",
                value=role["name"] if is_edit else "",
                hint_text="Ej: Supervisor, Vendedor...",
                bgcolor=T.SURFACE,
                border_color=T.BORDER_STRONG,
                focused_border_color=T.INDIGO,
                color=T.TEXT,
                label_style=ft.TextStyle(color=T.TEXT_MUTED),
                border_radius=10,
            )

            desc_input = ft.TextField(
                label="Descripción",
                value=role.get("description", "") if is_edit else "",
                hint_text="Descripción de funciones o permisos del rol...",
                multiline=True,
                min_lines=2,
                max_lines=2,
                bgcolor=T.SURFACE,
                border_color=T.BORDER_STRONG,
                focused_border_color=T.INDIGO,
                color=T.TEXT,
                label_style=ft.TextStyle(color=T.TEXT_MUTED),
                border_radius=10,
            )

            permission_checks: dict[str, dict[str, ft.Checkbox]] = {}
            current_role_id = (AppState.current_user or {}).get("role_id")
            is_own_role = bool(
                is_edit
                and current_role_id
                and int(role_id) == int(current_role_id)
            )

            def on_action_change(e, module_key: str, action: str):
                checks = permission_checks[module_key]
                if action != "can_read" and e.control.value:
                    # Crear/editar/eliminar sin ver no tiene sentido.
                    checks["can_read"].value = True
                elif action == "can_read" and not e.control.value:
                    for other_action, checkbox in checks.items():
                        if other_action != "can_read":
                            checkbox.value = False
                self.page.update()

            module_rows = []
            for module in MODULES:
                key = module["key"]
                current = current_permissions.get(key, {})
                checks = {}
                checkboxes = []
                for action in module["actions"]:
                    checkbox = ft.Checkbox(
                        label=ACTION_LABELS[action],
                        value=bool(current.get(action, False)),
                        fill_color=getattr(T, ACTION_COLORS[action], T.INDIGO),
                        label_style=ft.TextStyle(size=11, color=T.TEXT_SECONDARY),
                        width=checkbox_width,
                    )
                    checkbox.on_change = (
                        lambda e, k=key, a=action: on_action_change(e, k, a)
                    )
                    checks[action] = checkbox
                    checkboxes.append(checkbox)
                permission_checks[key] = checks

                module_icon = ft.Icon(
                    getattr(ft.Icons, module["icon"], ft.Icons.APPS),
                    size=18,
                    color=T.INDIGO_TEXT,
                )
                module_info = ft.Column(
                    controls=[
                        ft.Text(
                            module["label"],
                            size=12,
                            weight=ft.FontWeight.W_600,
                            color=T.TEXT,
                        ),
                        ft.Text(
                            module["description"],
                            size=10,
                            color=T.TEXT_SUBTLE,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                    spacing=0,
                    expand=True,
                )
                checkboxes_row = ft.Row(controls=checkboxes, spacing=2)

                if dialog_mobile:
                    module_content = ft.Column(
                        controls=[
                            ft.Row(
                                controls=[module_icon, module_info],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            checkboxes_row,
                        ],
                        spacing=4,
                    )
                else:
                    module_content = ft.Row(
                        controls=[module_icon, module_info, checkboxes_row],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )

                module_rows.append(
                    ft.Container(
                        content=module_content,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=5),
                        border_radius=8,
                        bgcolor=T.SURFACE,
                        border=_all_border(1, T.SURFACE_ALT),
                    )
                )

            def protect_own_role():
                """Evita que el usuario se quite a sí mismo el acceso a roles."""
                if not is_own_role:
                    return
                checks = permission_checks.get("roles", {})
                for action in ("can_read", "can_update"):
                    checkbox = checks.get(action)
                    if checkbox:
                        checkbox.value = True
                        checkbox.disabled = True

            protect_own_role()

            def apply_preset(preset_key: str):
                permissions = preset_permissions(preset_key)
                for key, checks in permission_checks.items():
                    for action, checkbox in checks.items():
                        checkbox.value = bool(
                            permissions.get(key, {}).get(action, False)
                        )
                protect_own_role()
                self.page.update()

            def clear_permissions(e=None):
                for checks in permission_checks.values():
                    for checkbox in checks.values():
                        checkbox.value = False
                protect_own_role()
                self.page.update()

            preset_buttons = [
                ft.OutlinedButton(
                    PRESETS[key]["label"],
                    tooltip=PRESETS[key]["description"],
                    on_click=lambda e, k=key: apply_preset(k),
                    style=ft.ButtonStyle(
                        color=T.INDIGO_TEXT,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                    ),
                )
                for key in PRESET_ORDER
                if key in PRESETS
            ]
            preset_buttons.append(
                ft.TextButton(
                    "Limpiar",
                    icon=ft.Icons.CLEAR_ALL_ROUNDED,
                    on_click=clear_permissions,
                    style=ft.ButtonStyle(color=T.TEXT_MUTED),
                )
            )

            permissions_title = ft.Text(
                "Acceso por módulo",
                color=T.TEXT_SECONDARY,
                size=13,
                weight=ft.FontWeight.BOLD,
            )
            permissions_hint = ft.Text(
                "Marca al menos un módulo",
                color=T.TEXT_SUBTLE,
                size=10,
            )
            permissions_header = (
                ft.Column(
                    controls=[permissions_title, permissions_hint],
                    spacing=0,
                )
                if dialog_width < 420
                else ft.Row(
                    controls=[permissions_title, permissions_hint],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )

            permissions_box = ft.Container(
                content=ft.Column(
                    controls=[
                        permissions_header,
                        ft.Column(
                            controls=[
                                ft.Row(controls=row, spacing=4)
                                for row in _chunk(
                                    preset_buttons,
                                    2 if dialog_width < 420
                                    else (3 if dialog_mobile else 4),
                                )
                            ],
                            spacing=4,
                        ),
                        ft.Text(
                            "No puedes quitarte a ti mismo el acceso a Roles "
                            "y permisos.",
                            color=T.AMBER,
                            size=10,
                            visible=is_own_role,
                        ),
                        ft.Column(
                            controls=module_rows,
                            spacing=4,
                        ),
                    ],
                    spacing=8,
                ),
                padding=10,
                border_radius=10,
                bgcolor=T.SURFACE_ALT,
                border=_all_border(1, T.BORDER_STRONG),
            )

            error_msg = ft.Text("", color=T.DANGER, size=12, visible=False)

            def save_role(e):
                error_msg.visible = False
                name_val = name_input.value
                desc_val = desc_input.value
                protect_own_role()
                permissions = {
                    key: {
                        action: bool(checkbox.value)
                        for action, checkbox in checks.items()
                    }
                    for key, checks in permission_checks.items()
                }

                if is_edit:
                    success, res = RoleController.update(
                        role_id=role_id,
                        name=name_val,
                        description=desc_val,
                        permissions=permissions,
                    )
                else:
                    success, res = RoleController.create(
                        name=name_val,
                        description=desc_val,
                        permissions=permissions,
                    )

                if success:
                    close_dialog(dialog)
                    load_roles()
                    show_toast(
                        "Rol actualizado exitosamente"
                        if is_edit
                        else "Rol creado exitosamente"
                    )
                else:
                    error_msg.value = str(res)
                    error_msg.visible = True
                    self.page.update()

            page_height = getattr(self.page, "height", None) or 800
            content_height = min(620, max(260, int(page_height) - 260))

            dialog = ft.AlertDialog(
                title=ft.Text(
                    "Editar Rol y Permisos" if is_edit else "Nuevo Rol",
                    color=T.TEXT,
                    weight=ft.FontWeight.BOLD,
                ),
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
                        scroll=ft.ScrollMode.AUTO,
                        height=content_height,
                    ),
                    width=dialog_width,
                ),
                actions=[
                    ft.TextButton(
                        "Cancelar",
                        on_click=lambda e: close_dialog(dialog),
                        style=ft.ButtonStyle(color=T.TEXT_MUTED),
                    ),
                    ft.FilledButton(
                        "Guardar",
                        on_click=save_role,
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

        # ── Diálogo eliminar rol ───────────────────────────────────────────
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
                        ft.Icon(
                            ft.Icons.WARNING_ROUNDED,
                            color=T.AMBER,
                            size=28,
                        ),
                        ft.Text(
                            "Confirmar eliminación",
                            color=T.TEXT,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                    spacing=10,
                ),
                content=ft.Text(
                    f"¿Estás seguro de que deseas eliminar el rol '{role_name}'?\n"
                    "Esta acción no se puede deshacer.",
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

        def on_search_change(e):
            self.filter_query = e.control.value
            render_roles()

        search_bar = ft.TextField(
            hint_text="Buscar roles por nombre o descripción...",
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

        new_role_btn = ft.FilledButton(
            "Nuevo Rol",
            icon=ft.Icons.ADD_ROUNDED,
            visible=AppState.has_permission("can_write", "roles"),
            style=ft.ButtonStyle(
                bgcolor=T.INDIGO,
                color=T.ON_ACCENT,
                padding=16,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            on_click=lambda e: open_role_dialog(),
        )

        header = ft.ResponsiveRow(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(
                                    ft.Icons.ADMIN_PANEL_SETTINGS_ROUNDED,
                                    color=T.ON_ACCENT,
                                    size=28,
                                ),
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
                                        "Gestión de Roles y Permisos",
                                        color=T.TEXT,
                                        size=24,
                                        weight=ft.FontWeight.BOLD,
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        "Asigna acceso por módulo: un vendedor "
                                        "puede usar POS y clientes; un bodeguero, "
                                        "solo inventario.",
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
                        controls=[new_role_btn],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    col={"xs": 12, "md": 4},
                ),
            ],
            spacing=12,
            run_spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        toolbar = ft.Row(
            controls=[search_bar],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        content_layout = ft.Container(
            content=ft.Column(
                controls=[
                    header,
                    ft.Divider(color=T.SURFACE_ALT, height=24),
                    toolbar,
                    ft.Container(height=8),
                    self.roles_container,
                ],
                spacing=12,
                expand=True,
            ),
            padding=12 if mobile else 24,
            expand=True,
        )

        load_roles()

        return MainLayout(
            page=self.page,
            content=content_layout,
            router=self.router,
        )
