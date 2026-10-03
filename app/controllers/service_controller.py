from app.models.service_model import ServiceModel

class ServiceController:
    @classmethod
    def get_all(cls):
        """Retorna todos los servicios."""
        return ServiceModel.all()

    @classmethod
    def get_by_id(cls, service_id: int):
        return ServiceModel.find(service_id)

    @classmethod
    def create(cls, codigo: str, nombre: str, descripcion: str = "", precio: float = 0.0, iva_porcentaje: float = 15.0, categoria: str = "Servicios", status: str = "active"):
        """Crea un nuevo servicio."""
        codigo = (codigo or "").strip().upper()
        nombre = (nombre or "").strip()

        if not codigo:
            return False, "El código del servicio es requerido."
        if not nombre:
            return False, "El nombre del servicio es requerido."

        try:
            precio_flt = float(precio)
            iva_flt = float(iva_porcentaje)
        except (ValueError, TypeError):
            return False, "Valores numéricos de precio o IVA inválidos."

        if precio_flt < 0:
            return False, "El precio no puede ser negativo."

        existing = ServiceModel.where(codigo=codigo)
        if existing:
            return False, f"Ya existe un servicio con el código '{codigo}'."

        new_service = ServiceModel.create(
            codigo=codigo,
            nombre=nombre,
            descripcion=(descripcion or "").strip(),
            precio=precio_flt,
            iva_porcentaje=iva_flt,
            categoria=categoria if categoria else "Servicios",
            status=status if status in ("active", "inactive") else "active"
        )
        return True, new_service

    @classmethod
    def update(cls, service_id: int, codigo: str, nombre: str, descripcion: str = "", precio: float = 0.0, iva_porcentaje: float = 15.0, categoria: str = "Servicios", status: str = "active"):
        """Actualiza un servicio existente."""
        codigo = (codigo or "").strip().upper()
        nombre = (nombre or "").strip()

        try:
            sid = int(service_id)
        except (ValueError, TypeError):
            return False, "ID de servicio inválido."

        service = ServiceModel.find(sid)
        if not service:
            return False, "Servicio no encontrado."

        if not codigo:
            return False, "El código es requerido."
        if not nombre:
            return False, "El nombre es requerido."

        try:
            precio_flt = float(precio)
            iva_flt = float(iva_porcentaje)
        except (ValueError, TypeError):
            return False, "Valores de precio o IVA inválidos."

        existing = ServiceModel.where(codigo=codigo)
        if existing and int(existing[0]["id"]) != sid:
            return False, f"Ya existe otro servicio con el código '{codigo}'."

        updated = ServiceModel.update_by_id(
            sid,
            codigo=codigo,
            nombre=nombre,
            descripcion=(descripcion or "").strip(),
            precio=precio_flt,
            iva_porcentaje=iva_flt,
            categoria=categoria if categoria else "Servicios",
            status=status if status in ("active", "inactive") else "active"
        )
        return True, updated

    @classmethod
    def delete(cls, service_id: int):
        """Elimina un servicio."""
        service = ServiceModel.find(service_id)
        if not service:
            return False, "Servicio no encontrado."
        ServiceModel.delete_by_id(service_id)
        return True, "Servicio eliminado exitosamente."
