import os
import re
import uuid
from pathlib import Path

from app.controllers.inventory_controller import InventoryController
from app.models.product_model import ProductModel
from app.models.supplier_model import SupplierModel
from core.database import transaction
from core.paths import GENERATED_DIR

PRODUCT_IMAGES_DIR = GENERATED_DIR / "products" / "images"
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _clean_source_path(source: str) -> str:
    """Normaliza una ruta elegida a mano o por el FilePicker."""
    path = (source or "").strip().strip('"').strip("'")
    if path.startswith("file://"):
        path = path[7:]
    return os.path.expanduser(path)


def _safe_filename_part(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", (value or "").strip())
    return cleaned.strip("_")[:50] or "producto"


class ProductController:
    @classmethod
    def get_all(cls):
        """Retorna todos los productos."""
        return ProductModel.all()

    @classmethod
    def get_by_id(cls, product_id: int):
        return ProductModel.find(product_id)

    @classmethod
    def _save_product_image(cls, source: str, codigo: str) -> tuple[str, str]:
        """Copia/optimiza la imagen y devuelve ``(ruta_final, error)``.

        Las imágenes se guardan fuera del código de la app para que sigan
        disponibles en Android después de una actualización. Se convierten a
        JPEG/PNG para que ReportLab pueda incrustarlas sin problemas.
        """
        path = _clean_source_path(source)
        if not path:
            return "", ""
        if not os.path.isfile(path):
            return "", "La imagen seleccionada no existe."

        extension = Path(path).suffix.lower()
        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            return "", "Formato de imagen no soportado. Usa JPG, PNG o WEBP."

        try:
            from PIL import Image as PILImage

            with PILImage.open(path) as image:
                image.load()
                image_format = (image.format or "").upper()
                if image_format not in ("JPEG", "JPG", "PNG", "WEBP"):
                    return "", "El archivo seleccionado no es una imagen válida."

                image.thumbnail((1400, 1400), PILImage.Resampling.LANCZOS)
                has_alpha = image.mode in ("RGBA", "LA") or "transparency" in image.info
                target_extension = ".png" if has_alpha else ".jpg"

                PRODUCT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
                filename = (
                    f"{_safe_filename_part(codigo)}_"
                    f"{uuid.uuid4().hex[:12]}{target_extension}"
                )
                target = PRODUCT_IMAGES_DIR / filename

                if has_alpha:
                    image.convert("RGBA").save(target, format="PNG", optimize=True)
                else:
                    image.convert("RGB").save(
                        target,
                        format="JPEG",
                        quality=88,
                        optimize=True,
                    )
        except Exception as exc:  # noqa: BLE001
            return "", f"No se pudo procesar la imagen: {exc}"

        return str(target), ""

    @classmethod
    def _remove_product_image(cls, image_path: str):
        """Elimina una imagen anterior solo si pertenece al directorio de productos."""
        path = _clean_source_path(image_path)
        if not path:
            return
        try:
            target = Path(path).resolve()
            images_dir = PRODUCT_IMAGES_DIR.resolve()
            if target.is_file() and target.is_relative_to(images_dir):
                target.unlink()
        except (OSError, ValueError):
            pass

    @classmethod
    def _resolve_supplier_id(cls, supplier_id):
        """Valida el proveedor opcional y devuelve ``(ok, id_o_error)``."""
        if supplier_id in (None, "", 0, "0"):
            return True, None
        try:
            sid = int(supplier_id)
        except (ValueError, TypeError):
            return False, "El proveedor seleccionado no es válido."
        if not SupplierModel.find(sid):
            return False, "El proveedor seleccionado no existe."
        return True, sid

    @classmethod
    def create(cls, codigo: str, nombre: str, descripcion: str = "", precio: float = 0.0, costo: float = 0.0, stock: int = 0, iva_porcentaje: float = 15.0, categoria: str = "General", status: str = "active", imagen_path: str = "", stock_minimo: int = 5, supplier_id=None):
        """Crea un nuevo producto."""
        codigo = (codigo or "").strip().upper()
        nombre = (nombre or "").strip()
        descripcion = (descripcion or "").strip()

        if not codigo:
            return False, "El código del producto es requerido."
        if not nombre:
            return False, "El nombre del producto es requerido."

        supplier_ok, supplier_value = cls._resolve_supplier_id(supplier_id)
        if not supplier_ok:
            return False, supplier_value

        try:
            precio_flt = float(precio)
            costo_flt = float(costo)
            stock_int = int(stock)
            iva_flt = float(iva_porcentaje)
            stock_minimo_int = int(stock_minimo)
        except (ValueError, TypeError):
            return False, "Valores numéricos de precio, costo, stock, stock mínimo o IVA inválidos."

        if precio_flt < 0:
            return False, "El precio no puede ser negativo."
        if stock_int < 0:
            return False, "El stock no puede ser negativo."
        if stock_minimo_int < 0:
            return False, "El stock mínimo no puede ser negativo."

        existing = ProductModel.where(codigo=codigo)
        if existing:
            return False, f"Ya existe un producto con el código '{codigo}'."

        saved_image, image_error = cls._save_product_image(imagen_path, codigo)
        if image_error:
            return False, image_error

        try:
            with transaction():
                new_product = ProductModel.create(
                    codigo=codigo,
                    nombre=nombre,
                    descripcion=descripcion,
                    precio=precio_flt,
                    costo=costo_flt,
                    stock=stock_int,
                    iva_porcentaje=iva_flt,
                    categoria=categoria if categoria else "General",
                    status=status if status in ("active", "inactive") else "active",
                    imagen_path=saved_image,
                    stock_minimo=stock_minimo_int,
                    supplier_id=supplier_value,
                )
                if stock_int > 0:
                    InventoryController.log_stock_change(
                        new_product["id"],
                        stock_anterior=0,
                        stock_nuevo=stock_int,
                        motivo="Stock inicial del producto",
                        referencia=codigo,
                        tipo="INICIAL",
                    )
        except Exception:
            cls._remove_product_image(saved_image)
            raise
        return True, new_product

    @classmethod
    def update(cls, product_id: int, codigo: str, nombre: str, descripcion: str = "", precio: float = 0.0, costo: float = 0.0, stock: int = 0, iva_porcentaje: float = 15.0, categoria: str = "General", status: str = "active", imagen_path: str | None = None, stock_minimo: int | None = None, supplier_id=None):
        """Actualiza un producto existente.

        ``imagen_path=None`` conserva la imagen actual; una cadena vacía la
        elimina y una ruta nueva reemplaza la anterior. ``stock_minimo=None``
        conserva el mínimo actual. ``supplier_id=None`` deja el producto sin
        proveedor.
        """
        codigo = (codigo or "").strip().upper()
        nombre = (nombre or "").strip()

        try:
            pid = int(product_id)
        except (ValueError, TypeError):
            return False, "ID de producto inválido."

        product = ProductModel.find(pid)
        if not product:
            return False, "Producto no encontrado."

        if not codigo:
            return False, "El código es requerido."
        if not nombre:
            return False, "El nombre es requerido."

        supplier_ok, supplier_value = cls._resolve_supplier_id(supplier_id)
        if not supplier_ok:
            return False, supplier_value

        try:
            precio_flt = float(precio)
            costo_flt = float(costo)
            stock_int = int(stock)
            iva_flt = float(iva_porcentaje)
            if stock_minimo is None:
                current_minimum = product.get("stock_minimo")
                stock_minimo_int = int(
                    current_minimum if current_minimum is not None else 5
                )
            else:
                stock_minimo_int = int(stock_minimo)
        except (ValueError, TypeError):
            return False, "Valores de precio, costo, stock, stock mínimo o IVA inválidos."
        if stock_minimo_int < 0:
            return False, "El stock mínimo no puede ser negativo."

        existing = ProductModel.where(codigo=codigo)
        if existing and int(existing[0]["id"]) != pid:
            return False, f"Ya existe otro producto con el código '{codigo}'."

        old_image = str(product.get("imagen_path") or "")
        final_image = old_image
        if imagen_path is not None:
            source_image = _clean_source_path(imagen_path)
            if source_image and source_image == _clean_source_path(old_image):
                final_image = old_image
            elif source_image:
                final_image, image_error = cls._save_product_image(source_image, codigo)
                if image_error:
                    return False, image_error
            else:
                final_image = ""

        old_stock = int(product.get("stock") or 0)
        try:
            with transaction():
                updated = ProductModel.update_by_id(
                    pid,
                    codigo=codigo,
                    nombre=nombre,
                    descripcion=(descripcion or "").strip(),
                    precio=precio_flt,
                    costo=costo_flt,
                    stock=stock_int,
                    iva_porcentaje=iva_flt,
                    categoria=categoria if categoria else "General",
                    status=status if status in ("active", "inactive") else "active",
                    imagen_path=final_image,
                    stock_minimo=stock_minimo_int,
                    supplier_id=supplier_value,
                )
                if old_stock != stock_int:
                    InventoryController.log_stock_change(
                        pid,
                        stock_anterior=old_stock,
                        stock_nuevo=stock_int,
                        motivo="Ajuste desde la edición del producto",
                        referencia=codigo,
                    )
        except Exception:
            if final_image != old_image:
                cls._remove_product_image(final_image)
            raise

        if final_image != old_image:
            cls._remove_product_image(old_image)
        return True, updated

    @classmethod
    def delete(cls, product_id: int):
        """Elimina un producto."""
        product = ProductModel.find(product_id)
        if not product:
            return False, "Producto no encontrado."
        ProductModel.delete_by_id(product_id)
        return True, "Producto eliminado exitosamente."
