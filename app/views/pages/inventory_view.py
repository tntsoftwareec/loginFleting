import flet as ft
from core import theme as T
from app.views.layouts.main_layout import MainLayout
from app.controllers.inventory_controller import InventoryController
from app.views.ui_helpers import (
    close_dialog,
    is_mobile_page,
    open_dialog,
    show_toast,
    stat_card,
    wide_dialog_width,
)
from core.state import AppState


def _all_border(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)


class InventoryView:
    def __init__(self, page: ft.Page, router):
        self.page = page
        self.router = router
        self.products = []
        self.search_query = ""
        self.filter_mode = "todos"
        self.products_container = ft.Column(
            spacing=10,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

    def render(self):
        if not AppState.has_permission("can_read", "inventory"):
            content_layout = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.LOCK_OUTLINED, color=T.DANGER, size=64),
                        ft.Text("Acceso Restringido", color=T.TEXT, size=22, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "No tienes permisos suficientes para acceder a este módulo.",
                            color=T.TEXT_MUTED,
                            size=14,
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
            return MainLayout(page=self.page, content=content_layout, router=self.router)

        can_write = AppState.has_permission("can_write", "inventory")
        stats_row = ft.ResponsiveRow(spacing=10, run_spacing=10)

        def stock_status(product):
            stock = int(product.get("stock") or 0)
            minimum = int(product.get("stock_minimo") or 0)
            if stock <= 0:
                return "Agotado", T.DANGER_TEXT, T.DANGER_BG
            if stock <= minimum:
                return "Bajo stock", T.WARNING, T.WARNING_BG
            return "Disponible", T.SUCCESS_TEXT, T.SUCCESS_BG

        def refresh_stats():
            summary = InventoryController.get_summary()
            stats_row.controls = [
                stat_card(
                    "Productos",
                    str(summary["products"]),
                    ft.Icons.INVENTORY_2_ROUNDED,
                    T.PURPLE,
                ),
                stat_card(
                    "Unidades en stock",
                    f'{summary["units"]:,}',
                    ft.Icons.WAREHOUSE_ROUNDED,
                    T.SKY,
                ),
                stat_card(
                    "Bajo stock",
                    str(summary["low_stock_total"]),
                    ft.Icons.WARNING_AMBER_ROUNDED,
                    T.WARNING,
                    subtitle=f'{summary["out_of_stock"]} agotado(s)',
                ),
                stat_card(
                    "Valor al costo",
                    f'${summary["inventory_value"]:,.2f}',
                    ft.Icons.ATTACH_MONEY_ROUNDED,
                    T.SUCCESS_TEXT,
                ),
            ]

        def find_product(product_id):
            for product in self.products:
                if str(product.get("id")) == str(product_id):
                    return product
            return None

        def open_movement_dialog(product=None, initial_type="ENTRADA"):
            selected_id = str(product["id"]) if product else None
            product_options = [
                ft.dropdown.Option(
                    str(p["id"]),
                    f'{p["codigo"]} · {p["nombre"]} (Stock: {p["stock"]})',
                )
                for p in sorted(
                    self.products,
                    key=lambda item: item.get("nombre", "").lower(),
                )
            ]

            dd_product = ft.Dropdown(
                label="Producto",
                value=selected_id,
                options=product_options,
                enable_search=True,
                expand=True,
            )
            dd_type = ft.Dropdown(
                label="Tipo de movimiento",
                value=initial_type,
                options=[
                    ft.dropdown.Option("ENTRADA", "Entrada de mercancía"),
                    ft.dropdown.Option("SALIDA", "Salida de mercancía"),
                    ft.dropdown.Option("AJUSTE", "Ajuste de stock"),
                ],
                expand=True,
            )
            tf_quantity = ft.TextField(
                label="Cantidad",
                value="1",
                expand=True,
                visible=initial_type != "AJUSTE",
            )
            tf_new_stock = ft.TextField(
                label="Nuevo stock",
                value=str(product.get("stock", 0)) if product else "0",
                expand=True,
                visible=initial_type == "AJUSTE",
            )
            tf_reason = ft.TextField(
                label="Motivo / Observación",
                hint_text="Compra, merma, devolución, corrección...",
                expand=True,
            )
            tf_reference = ft.TextField(
                label="Referencia (opcional)",
                hint_text="Factura de compra, guía, documento...",
                expand=True,
            )

            stock_info = ft.Text(
                "",
                size=12,
                color=T.TEXT_MUTED,
            )

            def refresh_stock_info():
                selected = find_product(dd_product.value)
                if selected:
                    stock_info.value = (
                        f'Stock actual: {selected["stock"]} · '
                        f'Mínimo: {selected["stock_minimo"]} · '
                        f'Categoría: {selected.get("categoria") or "General"}'
                    )
                    if dd_type.value == "AJUSTE" and tf_new_stock.value in ("", "0"):
                        tf_new_stock.value = str(selected["stock"])
                else:
                    stock_info.value = "Selecciona un producto para ver su stock actual."
                self.page.update()

            def on_type_change(e):
                is_adjustment = dd_type.value == "AJUSTE"
                tf_quantity.visible = not is_adjustment
                tf_new_stock.visible = is_adjustment
                if is_adjustment:
                    selected = find_product(dd_product.value)
                    if selected:
                        tf_new_stock.value = str(selected["stock"])
                refresh_stock_info()

            def on_product_change(e):
                refresh_stock_info()

            dd_type.on_select = on_type_change
            dd_product.on_select = on_product_change
            refresh_stock_info()

            def save_movement(e):
                selected = find_product(dd_product.value)
                if not selected:
                    show_toast(self.page, "Selecciona un producto.", is_error=True)
                    return

                movement_type = dd_type.value
                if movement_type == "AJUSTE":
                    success, result = InventoryController.set_stock(
                        selected["id"],
                        tf_new_stock.value,
                        motivo=tf_reason.value,
                        referencia=tf_reference.value,
                    )
                else:
                    success, result = InventoryController.register_movement(
                        selected["id"],
                        movement_type,
                        tf_quantity.value,
                        motivo=tf_reason.value,
                        referencia=tf_reference.value,
                    )

                if not success:
                    show_toast(self.page, str(result), is_error=True)
                    return

                close_dialog(self.page, dlg)
                show_toast(self.page, "Movimiento de inventario registrado correctamente.")
                load_data()

            dlg = ft.AlertDialog(
                title=ft.Text("Registrar movimiento de inventario", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            dd_product,
                            stock_info,
                            ft.Divider(height=1),
                            dd_type,
                            ft.Row([tf_quantity, tf_new_stock], spacing=10),
                            tf_reason,
                            tf_reference,
                        ],
                        tight=True,
                        spacing=12,
                    ),
                    width=wide_dialog_width(self.page, 500),
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: close_dialog(self.page, dlg)),
                    ft.FilledButton(
                        "Guardar movimiento",
                        icon=ft.Icons.SAVE_ROUNDED,
                        style=ft.ButtonStyle(bgcolor=T.PRIMARY, color=T.ON_ACCENT),
                        on_click=save_movement,
                    ),
                ],
            )
            open_dialog(self.page, dlg)

        def movement_type_chip(movement):
            movement_type = (movement.get("tipo") or "").upper()
            labels = {
                "ENTRADA": ("Entrada", T.SUCCESS_TEXT, T.SUCCESS_BG),
                "SALIDA": ("Salida", T.DANGER_TEXT, T.DANGER_BG),
                "VENTA": ("Venta", T.DANGER_TEXT, T.DANGER_BG),
                "AJUSTE": ("Ajuste", T.WARNING, T.WARNING_BG),
                "INICIAL": ("Inicial", T.INFO_TEXT, T.INFO_BG),
            }
            label, color, bgcolor = labels.get(
                movement_type,
                (movement_type or "Movimiento", T.TEXT_MUTED, T.SURFACE_ALT),
            )
            return ft.Container(
                content=ft.Text(
                    label,
                    size=10,
                    color=color,
                    weight=ft.FontWeight.BOLD,
                ),
                bgcolor=bgcolor,
                padding=ft.Padding.symmetric(horizontal=7, vertical=3),
                border_radius=10,
            )

        def open_history_dialog(product=None):
            movements = InventoryController.get_movements(
                product_id=product["id"] if product else None,
                limit=300,
            )
            title = (
                f'Movimientos: {product["codigo"]} · {product["nombre"]}'
                if product
                else "Historial general de inventario"
            )

            if not movements:
                content = ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.HISTORY_ROUNDED, size=42, color=T.ICON_MUTED),
                            ft.Text(
                                "Todavía no hay movimientos registrados.",
                                color=T.TEXT_MUTED,
                                size=14,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=30,
                    alignment=ft.Alignment(0, 0),
                )
            elif is_mobile_page(self.page):
                cards = []
                for movement in movements:
                    product_line = (
                        f'{movement.get("product_codigo") or ""} · '
                        f'{movement.get("product_nombre") or ""}'
                    )
                    cards.append(
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            movement_type_chip(movement),
                                            ft.Text(
                                                str(movement.get("created_at") or "")[:19],
                                                size=10,
                                                color=T.TEXT_SUBTLE,
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    ),
                                    ft.Text(
                                        product_line,
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        color=T.TEXT,
                                    ),
                                    ft.Text(
                                        f'Cantidad: {movement.get("cantidad")} · '
                                        f'Stock: {movement.get("stock_anterior")} → '
                                        f'{movement.get("stock_nuevo")}',
                                        size=11,
                                        color=T.TEXT_MUTED,
                                    ),
                                    ft.Text(
                                        movement.get("motivo") or "-",
                                        size=11,
                                        color=T.TEXT,
                                    ),
                                    *(
                                        [
                                            ft.Text(
                                                f'Ref: {movement.get("referencia")}',
                                                size=10,
                                                color=T.TEXT_SUBTLE,
                                            )
                                        ]
                                        if movement.get("referencia")
                                        else []
                                    ),
                                ],
                                spacing=5,
                            ),
                            padding=12,
                            bgcolor=T.SURFACE,
                            border_radius=8,
                            border=_all_border(1, T.SURFACE_ALT),
                        )
                    )
                content = ft.Column(
                    controls=cards,
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                    height=430,
                )
            else:
                rows = []
                for movement in movements:
                    movement_type = (movement.get("tipo") or "").upper()
                    sign = "+" if movement_type in ("ENTRADA", "INICIAL") else (
                        "-" if movement_type in ("SALIDA", "VENTA") else ""
                    )
                    rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(
                                    ft.Text(
                                        str(movement.get("created_at") or "")[:19],
                                        size=10,
                                    )
                                ),
                                ft.DataCell(
                                    ft.Text(
                                        f'{movement.get("product_codigo") or ""} · '
                                        f'{movement.get("product_nombre") or ""}',
                                        size=11,
                                    )
                                ),
                                ft.DataCell(movement_type_chip(movement)),
                                ft.DataCell(
                                    ft.Text(
                                        f'{sign}{movement.get("cantidad", 0)}',
                                        size=11,
                                        weight=ft.FontWeight.BOLD,
                                    )
                                ),
                                ft.DataCell(
                                    ft.Text(str(movement.get("stock_anterior", 0)), size=11)
                                ),
                                ft.DataCell(
                                    ft.Text(str(movement.get("stock_nuevo", 0)), size=11)
                                ),
                                ft.DataCell(
                                    ft.Text(movement.get("motivo") or "-", size=11)
                                ),
                                ft.DataCell(
                                    ft.Text(movement.get("referencia") or "-", size=10)
                                ),
                            ]
                        )
                    )

                content = ft.Column(
                    controls=[
                        ft.DataTable(
                            columns=[
                                ft.DataColumn(ft.Text("FECHA", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                                ft.DataColumn(ft.Text("PRODUCTO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                                ft.DataColumn(ft.Text("TIPO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                                ft.DataColumn(ft.Text("CANT.", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                                ft.DataColumn(ft.Text("ANTES", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                                ft.DataColumn(ft.Text("DESPUÉS", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                                ft.DataColumn(ft.Text("MOTIVO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                                ft.DataColumn(ft.Text("REFERENCIA", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                            ],
                            rows=rows,
                            heading_row_color=T.SURFACE_ALT,
                            horizontal_margin=12,
                            column_spacing=16,
                        )
                    ],
                    height=430,
                    scroll=ft.ScrollMode.AUTO,
                )

            dlg = ft.AlertDialog(
                title=ft.Text(title, weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=content,
                    width=wide_dialog_width(self.page, 1050),
                ),
                actions=[
                    ft.OutlinedButton(
                        "Cerrar",
                        on_click=lambda e: close_dialog(self.page, dlg),
                    ),
                ],
            )
            open_dialog(self.page, dlg)

        def render_inventory():
            self.products_container.controls.clear()
            query = self.search_query.strip().lower()
            filtered = []

            for product in self.products:
                stock = int(product.get("stock") or 0)
                minimum = int(product.get("stock_minimo") or 0)
                if self.filter_mode == "bajo" and not (0 < stock <= minimum):
                    continue
                if self.filter_mode == "agotados" and stock > 0:
                    continue
                if self.filter_mode == "disponibles" and stock <= minimum:
                    continue

                haystack = " ".join(
                    str(product.get(key) or "")
                    for key in ("codigo", "nombre", "categoria")
                ).lower()
                if query and query not in haystack:
                    continue
                filtered.append(product)

            if not filtered:
                self.products_container.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=48, color=T.ICON_MUTED),
                                ft.Text(
                                    "No se encontraron productos con ese filtro.",
                                    color=T.TEXT_MUTED,
                                    size=16,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        padding=40,
                        alignment=ft.Alignment(0, 0),
                    )
                )
                self.page.update()
                return

            rows = []
            cards = []
            for product in filtered:
                status_text, status_color, status_bg = stock_status(product)
                stock_value = int(product.get("stock") or 0)
                minimum = int(product.get("stock_minimo") or 0)
                value = float(product.get("valor_stock") or 0)

                status_chip = ft.Container(
                    content=ft.Text(
                        status_text,
                        size=10,
                        color=status_color,
                        weight=ft.FontWeight.BOLD,
                    ),
                    bgcolor=status_bg,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    border_radius=10,
                )

                stock_chip = ft.Container(
                    content=ft.Text(
                        f"{stock_value} unidades",
                        size=11,
                        color=status_color,
                        weight=ft.FontWeight.BOLD,
                    ),
                    bgcolor=status_bg,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    border_radius=12,
                )

                actions = ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED,
                            icon_color=T.SUCCESS_TEXT,
                            tooltip="Registrar entrada",
                            on_click=lambda e, p=product: open_movement_dialog(p, "ENTRADA"),
                            disabled=not can_write,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.REMOVE_CIRCLE_OUTLINE_ROUNDED,
                            icon_color=T.DANGER_TEXT,
                            tooltip="Registrar salida",
                            on_click=lambda e, p=product: open_movement_dialog(p, "SALIDA"),
                            disabled=not can_write,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.TUNE_ROUNDED,
                            icon_color=T.INFO_TEXT,
                            tooltip="Ajustar stock",
                            on_click=lambda e, p=product: open_movement_dialog(p, "AJUSTE"),
                            disabled=not can_write,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.HISTORY_ROUNDED,
                            icon_color=T.PURPLE_TEXT,
                            tooltip="Ver historial de movimientos",
                            on_click=lambda e, p=product: open_history_dialog(p),
                        ),
                    ],
                    spacing=0,
                )

                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(
                                ft.Text(
                                    product.get("codigo") or "",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=T.PURPLE_TEXT,
                                )
                            ),
                            ft.DataCell(
                                ft.Text(
                                    product.get("nombre") or "",
                                    size=13,
                                    weight=ft.FontWeight.W_500,
                                )
                            ),
                            ft.DataCell(
                                ft.Text(
                                    product.get("categoria") or "General",
                                    size=11,
                                    color=T.TEXT_MUTED,
                                )
                            ),
                            ft.DataCell(stock_chip),
                            ft.DataCell(ft.Text(str(minimum), size=11)),
                            ft.DataCell(
                                ft.Text(f'${float(product.get("costo") or 0):.2f}', size=11)
                            ),
                            ft.DataCell(
                                ft.Text(f"${value:.2f}", size=11, weight=ft.FontWeight.BOLD)
                            ),
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
                                                ft.Text(
                                                    product.get("nombre") or "",
                                                    size=14,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=T.TEXT,
                                                ),
                                                ft.Text(
                                                    f'{product.get("codigo") or ""} · '
                                                    f'{product.get("categoria") or "General"}',
                                                    size=10,
                                                    color=T.TEXT_MUTED,
                                                ),
                                            ],
                                            spacing=2,
                                            expand=True,
                                        ),
                                        ft.Column(
                                            controls=[status_chip, stock_chip],
                                            spacing=5,
                                            horizontal_alignment=ft.CrossAxisAlignment.END,
                                        ),
                                    ],
                                    vertical_alignment=ft.CrossAxisAlignment.START,
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Text(
                                            f"Mínimo: {minimum}",
                                            size=11,
                                            color=T.TEXT_MUTED,
                                        ),
                                        ft.Text(
                                            f"Costo: ${float(product.get('costo') or 0):.2f}",
                                            size=11,
                                            color=T.TEXT_MUTED,
                                        ),
                                        ft.Text(
                                            f"Valor: ${value:.2f}",
                                            size=11,
                                            color=T.TEXT_MUTED,
                                        ),
                                    ],
                                    spacing=12,
                                    wrap=True,
                                ),
                                ft.Row(
                                    controls=[actions],
                                    alignment=ft.MainAxisAlignment.END,
                                    wrap=True,
                                ),
                            ],
                            spacing=8,
                        ),
                        padding=12,
                        bgcolor=T.SURFACE,
                        border_radius=10,
                        border=_all_border(1, T.SURFACE_ALT),
                    )
                )

            if is_mobile_page(self.page):
                self.products_container.controls.append(
                    ft.Column(controls=cards, spacing=10)
                )
            else:
                self.products_container.controls.append(
                    ft.Container(
                        content=ft.DataTable(
                            columns=[
                                ft.DataColumn(ft.Text("CÓDIGO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                                ft.DataColumn(ft.Text("PRODUCTO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                                ft.DataColumn(ft.Text("CATEGORÍA", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                                ft.DataColumn(ft.Text("STOCK", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                                ft.DataColumn(ft.Text("MÍNIMO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                                ft.DataColumn(ft.Text("COSTO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                                ft.DataColumn(ft.Text("VALOR", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                                ft.DataColumn(ft.Text("ESTADO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                                ft.DataColumn(ft.Text("ACCIONES", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                            ],
                            rows=rows,
                            heading_row_color=T.SURFACE_ALT,
                            horizontal_margin=12,
                            column_spacing=16,
                        ),
                        bgcolor=T.SURFACE,
                        border_radius=10,
                        border=_all_border(1, T.SURFACE_ALT),
                        padding=10,
                    )
                )
            self.page.update()

        def load_data():
            self.products = InventoryController.get_stock_products()
            refresh_stats()
            render_inventory()

        def on_search_change(e):
            self.search_query = e.control.value
            render_inventory()

        def on_filter_change(e):
            self.filter_mode = (
                getattr(e.control, "value", None)
                or dd_filter.value
                or "todos"
            )
            render_inventory()

        search_field = ft.TextField(
            hint_text="Buscar por código, producto o categoría...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=on_search_change,
            height=42,
            width=280,
            text_size=14,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=0),
        )

        dd_filter = ft.Dropdown(
            label="Filtrar existencias",
            value="todos",
            width=190,
            options=[
                ft.dropdown.Option("todos", "Todos"),
                ft.dropdown.Option("bajo", "Bajo stock"),
                ft.dropdown.Option("agotados", "Agotados"),
                ft.dropdown.Option("disponibles", "Disponibles"),
            ],
            on_select=on_filter_change,
        )

        btn_movement = ft.FilledButton(
            "Registrar movimiento",
            icon=ft.Icons.SWAP_VERT_ROUNDED,
            style=ft.ButtonStyle(bgcolor=T.PRIMARY, color=T.ON_ACCENT),
            height=42,
            disabled=not can_write,
            on_click=lambda e: open_movement_dialog(),
        )

        btn_history = ft.OutlinedButton(
            "Historial general",
            icon=ft.Icons.HISTORY_ROUNDED,
            height=42,
            on_click=lambda e: open_history_dialog(),
        )

        header_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.WAREHOUSE_ROUNDED, size=28, color=T.PURPLE),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        "Inventario",
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        color=T.TEXT,
                                    ),
                                    ft.Text(
                                        "Control de existencias, entradas, salidas, ajustes e historial de movimientos",
                                        size=12,
                                        color=T.TEXT_MUTED,
                                    ),
                                ],
                                spacing=0,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Row(
                        controls=[
                            search_field,
                            dd_filter,
                            btn_movement,
                            btn_history,
                        ],
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
                ft.Container(height=8),
                self.products_container,
            ],
            expand=True,
            spacing=10,
            scroll=ft.ScrollMode.AUTO if is_mobile_page(self.page) else None,
        )

        load_data()
        return MainLayout(page=self.page, content=main_content, router=self.router)
