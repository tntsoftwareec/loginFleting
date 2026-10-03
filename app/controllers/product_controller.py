from app.models.product_model import ProductModel

class ProductController:
    @classmethod
    def get_all(cls):
        """Retorna todos los productos."""
        return ProductModel.all()

    @classmethod
    def get_by_id(cls, product_id: int):
        return ProductModel.find(product_id)

    @classmethod
    def create(cls, codigo: str, nombre: str, descripcion: str = "", precio: float = 0.0, costo: float = 0.0, stock: int = 0, iva_porcentaje: float = 15.0, categoria: str = "General", status: str = "active"):
        """Crea un nuevo producto."""
        codigo = (codigo or "").strip().upper()
        nombre = (nombre or "").strip()
        descripcion = (descripcion or "").strip()

        if not codigo:
            return False, "El código del producto es requerido."
        if not nombre:
            return False, "El nombre del producto es requerido."

        try:
            precio_flt = float(precio)
            costo_flt = float(costo)
            stock_int = int(stock)
            iva_flt = float(iva_porcentaje)
        except (ValueError, TypeError):
            return False, "Valores numéricos de precio, costo, stock o IVA inválidos."

        if precio_flt < 0:
            return False, "El precio no puede ser negativo."
        if stock_int < 0:
            return False, "El stock no puede ser negativo."

        existing = ProductModel.where(codigo=codigo)
        if existing:
            return False, f"Ya existe un producto con el código '{codigo}'."

        new_product = ProductModel.create(
            codigo=codigo,
            nombre=nombre,
            descripcion=descripcion,
            precio=precio_flt,
            costo=costo_flt,
            stock=stock_int,
            iva_porcentaje=iva_flt,
            categoria=categoria if categoria else "General",
            status=status if status in ("active", "inactive") else "active"
        )
        return True, new_product

    @classmethod
    def update(cls, product_id: int, codigo: str, nombre: str, descripcion: str = "", precio: float = 0.0, costo: float = 0.0, stock: int = 0, iva_porcentaje: float = 15.0, categoria: str = "General", status: str = "active"):
        """Actualiza un producto existente."""
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

        try:
            precio_flt = float(precio)
            costo_flt = float(costo)
            stock_int = int(stock)
            iva_flt = float(iva_porcentaje)
        except (ValueError, TypeError):
            return False, "Valores de precio, costo, stock o IVA inválidos."

        existing = ProductModel.where(codigo=codigo)
        if existing and int(existing[0]["id"]) != pid:
            return False, f"Ya existe otro producto con el código '{codigo}'."

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
            status=status if status in ("active", "inactive") else "active"
        )
        return True, updated

    @classmethod
    def delete(cls, product_id: int):
        """Elimina un producto."""
        product = ProductModel.find(product_id)
        if not product:
            return False, "Producto no encontrado."
        ProductModel.delete_by_id(product_id)
        return True, "Producto eliminado exitosamente."
