import flet as ft
from app.views.layouts.main_layout import MainLayout
from app.controllers.product_controller import ProductController
from core.state import AppState

def _all_border(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)

class ProductsView:
    def __init__(self, page: ft.Page, router):
        self.page = page
        self.router = router
        self.products_list = []
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

        self.products_container = ft.Column(spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)

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
            self.products_list = ProductController.get_all()
            render_products()

        def render_products():
            self.products_container.controls.clear()

            filtered = []
            for p in self.products_list:
                q = self.search_query.lower()
                matches = (
                    not q or
                    q in p["codigo"].lower() or
                    q in p["nombre"].lower() or
                    q in (p.get("categoria") or "").lower()
                )
                if matches:
                    filtered.append(p)

            if not filtered:
                self.products_container.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=48, color="#64748b"),
                                ft.Text("No se encontraron productos", color="#94a3b8", size=16),
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
            for p in filtered:
                stk = int(p.get("stock", 0))
                if stk <= 5:
                    stock_color = "#f87171"
                    stock_bg = "#991b1b33"
                elif stk <= 15:
                    stock_color = "#fbbf24"
                    stock_bg = "#78350f33"
                else:
                    stock_color = "#34d399"
                    stock_bg = "#065f4633"

                stock_chip = ft.Container(
                    content=ft.Text(
                        f"{stk} unidades",
                        size=11,
                        color=stock_color,
                        weight=ft.FontWeight.BOLD,
                    ),
                    bgcolor=stock_bg,
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
                            tooltip="Editar producto" if can_update else "Sin permiso",
                            disabled=not can_update,
                            on_click=lambda e, prod=p: open_product_dialog(prod),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINED,
                            icon_color="#ef4444" if can_delete else "#64748b",
                            tooltip="Eliminar producto" if can_delete else "Sin permiso",
                            disabled=not can_delete,
                            on_click=lambda e, prod=p: open_delete_dialog(prod),
                        ),
                    ],
                    spacing=0,
                )

                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(p["codigo"], size=12, weight=ft.FontWeight.BOLD, color="#60a5fa")),
                            ft.DataCell(ft.Text(p["nombre"], size=13, weight=ft.FontWeight.W_500)),
                            ft.DataCell(ft.Text(p.get("categoria") or "General", size=12)),
                            ft.DataCell(ft.Text(f"${float(p['precio']):.2f}", size=13, weight=ft.FontWeight.BOLD, color="#34d399")),
                            ft.DataCell(ft.Text(f"${float(p.get('costo', 0.0)):.2f}", size=12, color="#94a3b8")),
                            ft.DataCell(stock_chip),
                            ft.DataCell(ft.Text(f"{float(p.get('iva_porcentaje', 15.0)):.0f}%", size=12)),
                            ft.DataCell(actions),
                        ]
                    )
                )

            data_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("CÓDIGO", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("NOMBRE PRODUCTO", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("CATEGORÍA", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("PRECIO VENTA", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("COSTO", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("STOCK", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("IVA", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                    ft.DataColumn(ft.Text("ACCIONES", weight=ft.FontWeight.BOLD, color="#94a3b8")),
                ],
                rows=rows,
                heading_row_color="#1e293b",
                horizontal_margin=15,
                column_spacing=20,
            )

            self.products_container.controls.append(
                ft.Container(
                    content=data_table,
                    bgcolor="#0f172a",
                    border_radius=10,
                    border=_all_border(1, "#1e293b"),
                    padding=10,
                )
            )
            self.page.update()

        def open_product_dialog(prod=None):
            is_edit = prod is not None

            tf_cod = ft.TextField(
                label="Código del Producto",
                value=prod["codigo"] if is_edit else "",
                expand=True,
            )
            tf_nom = ft.TextField(
                label="Nombre del Producto",
                value=prod["nombre"] if is_edit else "",
                expand=True,
            )
            tf_cat = ft.TextField(
                label="Categoría",
                value=prod.get("categoria", "Tecnología") if is_edit else "General",
                expand=True,
            )
            tf_prec = ft.TextField(
                label="Precio de Venta ($)",
                value=str(prod["precio"]) if is_edit else "0.00",
                expand=True,
            )
            tf_cost = ft.TextField(
                label="Costo ($)",
                value=str(prod.get("costo", 0.0)) if is_edit else "0.00",
                expand=True,
            )
            tf_stk = ft.TextField(
                label="Stock Disponible",
                value=str(prod.get("stock", 0)) if is_edit else "10",
                expand=True,
            )
            tf_iva = ft.Dropdown(
                label="Tarifa IVA",
                value=str(int(float(prod.get("iva_porcentaje", 15.0)))) if is_edit else "15",
                options=[
                    ft.dropdown.Option("15", "IVA 15%"),
                    ft.dropdown.Option("0", "IVA 0%"),
                ],
                expand=True,
            )
            tf_desc = ft.TextField(
                label="Descripción / Detalles",
                value=prod.get("descripcion", "") if is_edit else "",
                multiline=True,
                max_lines=2,
                expand=True,
            )
            sw_status = ft.Switch(
                label="Producto Activo",
                value=(prod.get("status", "active") == "active") if is_edit else True,
            )

            def save_product(e):
                cod = tf_cod.value
                nom = tf_nom.value
                cat = tf_cat.value
                precio = tf_prec.value
                costo = tf_cost.value
                stock = tf_stk.value
                iva = tf_iva.value
                desc = tf_desc.value
                status = "active" if sw_status.value else "inactive"

                if is_edit:
                    success, res = ProductController.update(
                        prod["id"], cod, nom, desc, precio, costo, stock, iva, cat, status
                    )
                else:
                    success, res = ProductController.create(
                        cod, nom, desc, precio, costo, stock, iva, cat, status
                    )

                if success:
                    close_dialog(dlg)
                    show_toast("Producto guardado exitosamente.")
                    load_data()
                else:
                    show_toast(res, is_error=True)

            dlg = ft.AlertDialog(
                title=ft.Text("Editar Producto" if is_edit else "Nuevo Producto", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row([tf_cod, tf_cat], spacing=10),
                            tf_nom,
                            ft.Row([tf_prec, tf_cost], spacing=10),
                            ft.Row([tf_stk, tf_iva], spacing=10),
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
                        bgcolor="#2563eb",
                        color="#ffffff",
                        on_click=save_product,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            show_dialog(dlg)

        def open_delete_dialog(prod):
            def confirm_delete(e):
                success, msg = ProductController.delete(prod["id"])
                close_dialog(dlg)
                if success:
                    show_toast(msg)
                    load_data()
                else:
                    show_toast(msg, is_error=True)

            dlg = ft.AlertDialog(
                title=ft.Text("Confirmar Eliminación", color="#ef4444", weight=ft.FontWeight.BOLD),
                content=ft.Text(f"¿Estás seguro de eliminar el producto '{prod['nombre']}'?"),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg)),
                    ft.FilledButton("Eliminar", bgcolor="#ef4444", color="#ffffff", on_click=confirm_delete),
                ],
            )
            show_dialog(dlg)

        def on_search_change(e):
            self.search_query = e.control.value
            render_products()

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
            "Nuevo Producto",
            icon=ft.Icons.ADD,
            bgcolor="#2563eb" if can_write else "#475569",
            color="#ffffff",
            disabled=not can_write,
            on_click=lambda e: open_product_dialog(),
            height=42,
        )

        header_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.INVENTORY_2_ROUNDED, size=28, color="#a855f7"),
                            ft.Column(
                                controls=[
                                    ft.Text("Catálogo de Productos", size=20, weight=ft.FontWeight.BOLD, color="#f8fafc"),
                                    ft.Text("Inventario de mercancías, precios y control de stock", size=12, color="#94a3b8"),
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
                self.products_container,
            ],
            expand=True,
            spacing=0,
        )

        load_data()
        return MainLayout(page=self.page, content=main_content, router=self.router)
