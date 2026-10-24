"""Control de existencias y movimientos de inventario."""

from app.models.inventory_model import InventoryMovementModel
from app.models.product_model import ProductModel
from core.database import get_connection, transaction

DEFAULT_MIN_STOCK = 5


class InventoryController:
    @classmethod
    def _to_dicts(cls, cursor, rows):
        if not rows:
            return []
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    @classmethod
    def _normalize_product(cls, product: dict) -> dict:
        item = dict(product)
        item["stock"] = int(item.get("stock") or 0)
        minimum = item.get("stock_minimo")
        item["stock_minimo"] = int(
            minimum if minimum is not None else DEFAULT_MIN_STOCK
        )
        item["costo"] = float(item.get("costo") or 0)
        item["precio"] = float(item.get("precio") or 0)
        item["valor_stock"] = item["stock"] * item["costo"]
        return item

    @classmethod
    def get_stock_products(cls) -> list:
        """Productos con datos normalizados, priorizando los de bajo stock."""
        products = [cls._normalize_product(p) for p in ProductModel.all()]

        def sort_key(product):
            stock = product["stock"]
            minimum = product["stock_minimo"]
            if stock <= 0:
                level = 0
            elif stock <= minimum:
                level = 1
            else:
                level = 2
            return level, product.get("nombre", "").lower()

        return sorted(products, key=sort_key)

    @classmethod
    def get_summary(cls) -> dict:
        products = cls.get_stock_products()
        total_units = sum(p["stock"] for p in products)
        out_of_stock = sum(1 for p in products if p["stock"] <= 0)
        low_stock = sum(
            1 for p in products if 0 < p["stock"] <= p["stock_minimo"]
        )
        inventory_value = sum(p["valor_stock"] for p in products)
        return {
            "products": len(products),
            "units": total_units,
            "out_of_stock": out_of_stock,
            "low_stock": low_stock,
            "low_stock_total": out_of_stock + low_stock,
            "inventory_value": inventory_value,
        }

    @classmethod
    def get_movements(cls, product_id: int | None = None, limit: int = 250,
                      search: str = "") -> list:
        """Historial de movimientos, del más reciente al más antiguo."""
        clauses = []
        params = []

        if product_id:
            clauses.append("product_id = ?")
            params.append(int(product_id))

        search = (search or "").strip()
        if search:
            pattern = f"%{search}%"
            clauses.append(
                "(product_codigo LIKE ? OR product_nombre LIKE ? OR "
                "motivo LIKE ? OR referencia LIKE ? OR tipo LIKE ?)"
            )
            params.extend([pattern] * 5)

        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        try:
            safe_limit = max(1, min(int(limit), 1000))
        except (ValueError, TypeError):
            safe_limit = 250
        params.append(safe_limit)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM inventory_movements"
            f"{where} ORDER BY id DESC LIMIT ?",
            tuple(params),
        )
        return cls._to_dicts(cursor, cursor.fetchall())

    @classmethod
    def _default_reason(cls, tipo: str) -> str:
        return {
            "ENTRADA": "Entrada manual de inventario",
            "SALIDA": "Salida manual de inventario",
            "VENTA": "Venta",
            "AJUSTE": "Ajuste manual de stock",
            "INICIAL": "Stock inicial del producto",
        }.get(tipo, "Movimiento de inventario")

    @classmethod
    def _create_movement(cls, product: dict, tipo: str, cantidad: int,
                         stock_anterior: int, stock_nuevo: int,
                         motivo: str = "", referencia: str = "") -> dict:
        return InventoryMovementModel.create(
            product_id=product.get("id"),
            product_codigo=product.get("codigo") or "",
            product_nombre=product.get("nombre") or "",
            tipo=tipo,
            cantidad=int(cantidad),
            stock_anterior=int(stock_anterior),
            stock_nuevo=int(stock_nuevo),
            motivo=(motivo or "").strip() or cls._default_reason(tipo),
            referencia=(referencia or "").strip(),
        )

    @classmethod
    def register_movement(cls, product_id: int, tipo: str, cantidad: int,
                          motivo: str = "", referencia: str = ""):
        """Registra una entrada, salida o venta y actualiza el stock."""
        tipo = (tipo or "").strip().upper()
        if tipo not in ("ENTRADA", "SALIDA", "VENTA"):
            return False, "Tipo de movimiento inválido."

        try:
            pid = int(product_id)
            quantity = int(cantidad)
        except (ValueError, TypeError):
            return False, "Producto o cantidad inválidos."

        if quantity <= 0:
            return False, "La cantidad debe ser mayor a cero."

        with transaction():
            product = ProductModel.find(pid)
            if not product:
                return False, "Producto no encontrado."

            old_stock = int(product.get("stock") or 0)
            if tipo == "ENTRADA":
                new_stock = old_stock + quantity
            else:
                new_stock = old_stock - quantity
                if new_stock < 0:
                    return False, (
                        f"Stock insuficiente para '{product.get('nombre')}'. "
                        f"Disponible: {old_stock}, solicitado: {quantity}."
                    )

            movement = cls._create_movement(
                product,
                tipo=tipo,
                cantidad=quantity,
                stock_anterior=old_stock,
                stock_nuevo=new_stock,
                motivo=motivo,
                referencia=referencia,
            )
            ProductModel.update_by_id(pid, stock=new_stock)

        return True, movement

    @classmethod
    def set_stock(cls, product_id: int, nuevo_stock: int, motivo: str = "",
                  referencia: str = ""):
        """Fija el stock a un valor absoluto y deja un movimiento de ajuste."""
        try:
            pid = int(product_id)
            new_stock = int(nuevo_stock)
        except (ValueError, TypeError):
            return False, "Producto o stock inválido."

        if new_stock < 0:
            return False, "El stock no puede ser negativo."

        with transaction():
            product = ProductModel.find(pid)
            if not product:
                return False, "Producto no encontrado."

            old_stock = int(product.get("stock") or 0)
            if old_stock == new_stock:
                return False, "El stock nuevo es igual al stock actual."

            movement = cls._create_movement(
                product,
                tipo="AJUSTE",
                cantidad=abs(new_stock - old_stock),
                stock_anterior=old_stock,
                stock_nuevo=new_stock,
                motivo=motivo,
                referencia=referencia,
            )
            ProductModel.update_by_id(pid, stock=new_stock)

        return True, movement

    @classmethod
    def log_stock_change(cls, product_id: int, stock_anterior: int,
                         stock_nuevo: int, motivo: str = "",
                         referencia: str = "", tipo: str = "AJUSTE"):
        """Registra un cambio de stock ya aplicado (alta/edición de producto).

        No vuelve a actualizar el producto; se usa dentro de la transacción
        que guarda el producto para mantener el historial sincronizado.
        """
        old_stock = int(stock_anterior)
        new_stock = int(stock_nuevo)
        if old_stock == new_stock:
            return None

        product = ProductModel.find(product_id)
        if not product:
            return None

        return cls._create_movement(
            product,
            tipo=(tipo or "AJUSTE").upper(),
            cantidad=abs(new_stock - old_stock),
            stock_anterior=old_stock,
            stock_nuevo=new_stock,
            motivo=motivo,
            referencia=referencia,
        )
