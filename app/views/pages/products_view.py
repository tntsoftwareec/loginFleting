import os
import tempfile

import flet as ft
from core import theme as T
from app.views.layouts.main_layout import MainLayout
from app.controllers.product_controller import ProductController
from app.controllers.supplier_controller import SupplierController
from app.views.components.import_export import build_import_export_bar
from app.views.ui_helpers import get_file_picker, is_mobile_page
from core.state import AppState

def _all_border(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)


def _product_thumbnail(product: dict, size: int = 40):
    """Miniatura para el listado, o icono si el producto no tiene imagen."""
    path = str(product.get("imagen_path") or "").strip()
    if path and os.path.isfile(path):
        return ft.Container(
            content=ft.Image(
                src=path,
                width=size,
                height=size,
                fit=ft.BoxFit.COVER,
                border_radius=6,
                error_content=ft.Icon(
                    ft.Icons.BROKEN_IMAGE_OUTLINED,
                    size=max(14, int(size * 0.45)),
                    color=T.TEXT_SUBTLE,
                ),
            ),
            width=size,
            height=size,
            border_radius=6,
        )
    return ft.Container(
        content=ft.Icon(
            ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED,
            size=max(16, int(size * 0.5)),
            color=T.TEXT_SUBTLE,
        ),
        width=size,
        height=size,
        bgcolor=T.SURFACE_ALT,
        border_radius=6,
        alignment=ft.Alignment(0, 0),
    )

class ProductsView:
    def __init__(self, page: ft.Page, router):
        self.page = page
        self.router = router
        self.products_list = []
        self.suppliers_list = []
        self.search_query = ""

    def render(self):
        if not AppState.has_permission("can_read", "products"):
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
            self.products_list = ProductController.get_all()
            self.suppliers_list = SupplierController.get_all()
            render_products()

        def render_products():
            self.products_container.controls.clear()

            suppliers_by_id = {
                int(s["id"]): s.get("razon_social") or ""
                for s in self.suppliers_list
            }

            filtered = []
            for p in self.products_list:
                q = self.search_query.lower()
                supplier_name = suppliers_by_id.get(
                    int(p.get("supplier_id") or 0), ""
                )
                matches = (
                    not q or
                    q in p["codigo"].lower() or
                    q in p["nombre"].lower() or
                    q in (p.get("categoria") or "").lower() or
                    q in supplier_name.lower()
                )
                if matches:
                    filtered.append(p)

            if not filtered:
                self.products_container.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=48, color=T.ICON_MUTED),
                                ft.Text("No se encontraron productos", color=T.TEXT_MUTED, size=16),
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
            for p in filtered:
                stk = int(p.get("stock", 0))
                min_stock = int(p.get("stock_minimo", 5) or 0)
                supplier_name = suppliers_by_id.get(
                    int(p.get("supplier_id") or 0), ""
                ) or "Sin proveedor"
                if stk <= 0:
                    stock_color = T.DANGER_TEXT
                    stock_bg = T.DANGER_BG
                elif stk <= min_stock:
                    stock_color = T.WARNING
                    stock_bg = T.WARNING_BG
                else:
                    stock_color = T.SUCCESS_TEXT
                    stock_bg = T.SUCCESS_BG

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

                can_update = AppState.has_permission("can_update", "products")
                can_delete = AppState.has_permission("can_delete", "products")

                actions = ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            icon_color=T.INFO if can_update else T.TEXT_SUBTLE,
                            tooltip="Editar producto" if can_update else "Sin permiso",
                            disabled=not can_update,
                            on_click=lambda e, prod=p: open_product_dialog(prod),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINED,
                            icon_color=T.DANGER if can_delete else T.TEXT_SUBTLE,
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
                            ft.DataCell(ft.Text(p["codigo"], size=12, weight=ft.FontWeight.BOLD, color=T.INFO_TEXT)),
                            ft.DataCell(
                                ft.Row(
                                    controls=[
                                        _product_thumbnail(p, 34),
                                        ft.Text(p["nombre"], size=13, weight=ft.FontWeight.W_500),
                                    ],
                                    spacing=8,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                )
                            ),
                            ft.DataCell(ft.Text(p.get("categoria") or "General", size=12)),
                            ft.DataCell(ft.Text(supplier_name, size=12, color=T.TEXT_MUTED)),
                            ft.DataCell(ft.Text(f"${float(p['precio']):.2f}", size=13, weight=ft.FontWeight.BOLD, color=T.SUCCESS_TEXT)),
                            ft.DataCell(ft.Text(f"${float(p.get('costo', 0.0)):.2f}", size=12, color=T.TEXT_MUTED)),
                            ft.DataCell(stock_chip),
                            ft.DataCell(ft.Text(f"{float(p.get('iva_porcentaje', 15.0)):.0f}%", size=12)),
                            ft.DataCell(ft.Text(
                                f"{float(p.get('ice_porcentaje') or 0):.0f}%"
                                if float(p.get('ice_porcentaje') or 0) > 0 else "—",
                                size=12,
                            )),
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
                                        _product_thumbnail(p, 44),
                                        ft.Column(
                                            controls=[
                                                ft.Text(p["nombre"], size=15, weight=ft.FontWeight.BOLD, color=T.TEXT),
                                                ft.Text(f'{p["codigo"]} · {p.get("categoria") or "General"}', size=11, color=T.TEXT_MUTED),
                                                ft.Text(f"Proveedor: {supplier_name}", size=11, color=T.TEXT_SECONDARY),
                                            ],
                                            spacing=2,
                                            expand=True,
                                        ),
                                        stock_chip,
                                    ],
                                    vertical_alignment=ft.CrossAxisAlignment.START,
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Text(f"Venta: ${float(p['precio']):.2f}", size=13, weight=ft.FontWeight.BOLD, color=T.SUCCESS_TEXT),
                                        ft.Text(f"Costo: ${float(p.get('costo', 0.0)):.2f}", size=12, color=T.TEXT_MUTED),
                                        ft.Text(f"IVA {float(p.get('iva_porcentaje', 15.0)):.0f}%", size=12, color=T.TEXT_SECONDARY),
                                        *(
                                            [ft.Text(
                                                f"ICE {float(p.get('ice_porcentaje') or 0):.0f}%",
                                                size=12,
                                                color=T.WARNING,
                                            )]
                                            if float(p.get('ice_porcentaje') or 0) > 0 else []
                                        ),
                                    ],
                                    spacing=12,
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

            if is_mobile_page(self.page):
                self.products_container.controls.append(
                    ft.Column(controls=cards, spacing=10)
                )
            else:
                data_table = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("CÓDIGO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("NOMBRE PRODUCTO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("CATEGORÍA", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("PROVEEDOR", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("PRECIO VENTA", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("COSTO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("STOCK", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("IVA", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("ICE", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                        ft.DataColumn(ft.Text("ACCIONES", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
                    ],
                    rows=rows,
                    heading_row_color=T.SURFACE_ALT,
                    horizontal_margin=15,
                    column_spacing=20,
                )

                self.products_container.controls.append(
                    ft.Container(
                        content=data_table,
                        bgcolor=T.SURFACE,
                        border_radius=10,
                        border=_all_border(1, T.SURFACE_ALT),
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
            suppliers = self.suppliers_list or SupplierController.get_all()
            supplier_options = [ft.dropdown.Option("0", "Sin proveedor")]
            supplier_options.extend(
                ft.dropdown.Option(str(s["id"]), s.get("razon_social") or "")
                for s in suppliers
            )
            current_supplier = (
                str(prod.get("supplier_id") or "0") if is_edit else "0"
            )
            valid_supplier_keys = {"0"} | {str(s["id"]) for s in suppliers}
            if current_supplier not in valid_supplier_keys:
                current_supplier = "0"
            dd_supplier = ft.Dropdown(
                label="Proveedor",
                value=current_supplier,
                options=supplier_options,
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
            tf_min = ft.TextField(
                label="Stock Mínimo",
                value=str(
                    prod.get("stock_minimo")
                    if prod.get("stock_minimo") is not None else 5
                ) if is_edit else "5",
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
            tf_ice_codigo = ft.TextField(
                label="Código ICE SRI (opcional)",
                value=str(prod.get("ice_codigo") or "") if is_edit else "",
                hint_text="Ej: 3031",
                expand=True,
            )
            tf_ice_pct = ft.TextField(
                label="Tarifa ICE %",
                value=str(float(prod.get("ice_porcentaje") or 0)) if is_edit else "0",
                hint_text="0 = sin ICE",
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

            selected_image = {
                "path": str(prod.get("imagen_path") or "").strip() if is_edit else ""
            }
            image_preview_container = ft.Container(
                width=100,
                height=100,
                bgcolor=T.SURFACE_ALT,
                border_radius=8,
                alignment=ft.Alignment(0, 0),
            )

            def render_image_preview():
                path = selected_image["path"]
                if path and os.path.isfile(path):
                    image_preview_container.content = ft.Image(
                        src=path,
                        width=100,
                        height=100,
                        fit=ft.BoxFit.CONTAIN,
                        border_radius=8,
                        error_content=ft.Icon(
                            ft.Icons.BROKEN_IMAGE_OUTLINED,
                            size=30,
                            color=T.TEXT_SUBTLE,
                        ),
                    )
                else:
                    image_preview_container.content = ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED, size=30, color=T.ICON_MUTED),
                            ft.Text("Sin imagen", size=10, color=T.TEXT_MUTED),
                        ],
                        spacing=2,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                    )

            picker = get_file_picker(self.page)

            def pick_product_image(e):
                async def run():
                    try:
                        files = await picker.pick_files(
                            dialog_title="Seleccionar imagen del producto",
                            file_type=ft.FilePickerFileType.CUSTOM,
                            allowed_extensions=["jpg", "jpeg", "png", "webp"],
                            allow_multiple=False,
                            with_data=True,
                        )
                    except Exception as exc:  # noqa: BLE001
                        show_toast(
                            f"No se pudo abrir el selector de imágenes: {exc}",
                            is_error=True,
                        )
                        return

                    if not files:
                        return

                    chosen = files[0]
                    path = chosen.path

                    # Web/móvil pueden entregar solo los bytes; se guardan en
                    # un temporal para que el controlador pueda copiarlos.
                    if not path and chosen.bytes:
                        suffix = os.path.splitext(chosen.name or "")[1].lower() or ".jpg"
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                        tmp.write(chosen.bytes)
                        tmp.close()
                        path = tmp.name

                    if not path:
                        show_toast(
                            "No se pudo leer la imagen seleccionada. Intenta de nuevo.",
                            is_error=True,
                        )
                        return

                    selected_image["path"] = path
                    render_image_preview()
                    self.page.update()
                    show_toast(f"Imagen seleccionada: {chosen.name or os.path.basename(path)}")

                self.page.run_task(run)

            def clear_product_image(e):
                selected_image["path"] = ""
                render_image_preview()
                self.page.update()

            def save_product(e):
                cod = tf_cod.value
                nom = tf_nom.value
                cat = tf_cat.value
                precio = tf_prec.value
                costo = tf_cost.value
                stock = tf_stk.value
                stock_minimo = tf_min.value
                iva = tf_iva.value
                ice_codigo = tf_ice_codigo.value
                ice_porcentaje = tf_ice_pct.value
                desc = tf_desc.value
                status = "active" if sw_status.value else "inactive"
                supplier_id = dd_supplier.value

                if is_edit:
                    current_image = str(prod.get("imagen_path") or "").strip()
                    chosen_image = selected_image["path"]
                    # None conserva la imagen actual; "" la elimina.
                    image_arg = None if chosen_image == current_image else chosen_image
                    success, res = ProductController.update(
                        prod["id"], cod, nom, desc, precio, costo, stock, iva, cat, status,
                        imagen_path=image_arg,
                        stock_minimo=stock_minimo,
                        supplier_id=supplier_id,
                        ice_codigo=ice_codigo,
                        ice_porcentaje=ice_porcentaje,
                    )
                else:
                    success, res = ProductController.create(
                        cod, nom, desc, precio, costo, stock, iva, cat, status,
                        imagen_path=selected_image["path"],
                        stock_minimo=stock_minimo,
                        supplier_id=supplier_id,
                        ice_codigo=ice_codigo,
                        ice_porcentaje=ice_porcentaje,
                    )

                if success:
                    close_dialog(dlg)
                    show_toast("Producto guardado exitosamente.")
                    load_data()
                else:
                    show_toast(res, is_error=True)

            render_image_preview()

            dlg = ft.AlertDialog(
                title=ft.Text("Editar Producto" if is_edit else "Nuevo Producto", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row([tf_cod, tf_cat], spacing=10),
                            ft.Row([tf_nom, dd_supplier], spacing=10),
                            ft.Row([tf_prec, tf_cost], spacing=10),
                            ft.Row([tf_stk, tf_min, tf_iva], spacing=10),
                            ft.Row([tf_ice_codigo, tf_ice_pct], spacing=10),
                            ft.Text(
                                "El ICE solo aplica a bienes gravados con este impuesto. "
                                "Use el código de 4 dígitos del catálogo del SRI.",
                                size=10,
                                color=T.TEXT_MUTED,
                            ),
                            tf_desc,
                            ft.Row(
                                controls=[
                                    image_preview_container,
                                    ft.Column(
                                        controls=[
                                            ft.Text(
                                                "Imagen del producto",
                                                size=12,
                                                weight=ft.FontWeight.BOLD,
                                                color=T.TEXT_MUTED,
                                            ),
                                            ft.Text(
                                                "JPG, PNG o WEBP. Se usa en el PDF de las cotizaciones.",
                                                size=10,
                                                color=T.TEXT_MUTED,
                                            ),
                                            ft.Row(
                                                controls=[
                                                    ft.OutlinedButton(
                                                        "Seleccionar",
                                                        icon=ft.Icons.UPLOAD_FILE_ROUNDED,
                                                        on_click=pick_product_image,
                                                    ),
                                                    ft.TextButton(
                                                        "Quitar",
                                                        icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                                                        on_click=clear_product_image,
                                                    ),
                                                ],
                                                spacing=4,
                                            ),
                                        ],
                                        spacing=6,
                                        expand=True,
                                    ),
                                ],
                                spacing=12,
                                vertical_alignment=ft.CrossAxisAlignment.START,
                            ),
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
                title=ft.Text("Confirmar Eliminación", color=T.DANGER, weight=ft.FontWeight.BOLD),
                content=ft.Text(f"¿Estás seguro de eliminar el producto '{prod['nombre']}'?"),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: close_dialog(dlg)),
                    ft.FilledButton("Eliminar", bgcolor=T.DANGER, color=T.ON_ACCENT, on_click=confirm_delete),
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
            width=260,
            text_size=14,
            content_padding=ft.Padding.symmetric(horizontal=10, vertical=0),
        )

        can_write = AppState.has_permission("can_write", "products")
        btn_add = ft.FilledButton(
            "Nuevo Producto",
            icon=ft.Icons.ADD,
            bgcolor=T.PRIMARY if can_write else T.DISABLED_BG,
            color=T.ON_ACCENT,
            disabled=not can_write,
            on_click=lambda e: open_product_dialog(),
            height=42,
        )

        import_export_bar = build_import_export_bar(self.page, kind="products", on_changed=load_data)

        header_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.INVENTORY_2_ROUNDED, size=28, color=T.PURPLE),
                            ft.Column(
                                controls=[
                                    ft.Text("Catálogo de Productos", size=20, weight=ft.FontWeight.BOLD, color=T.TEXT),
                                    ft.Text("Inventario de mercancías, precios y control de stock", size=12, color=T.TEXT_MUTED),
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
                self.products_container,
            ],
            expand=True,
            spacing=0,
        )

        load_data()
        return MainLayout(page=self.page, content=main_content, router=self.router)
