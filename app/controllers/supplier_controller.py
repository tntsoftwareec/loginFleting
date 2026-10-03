import re
from app.models.supplier_model import SupplierModel

class SupplierController:
    @classmethod
    def get_all(cls):
        """Retorna todos los proveedores."""
        return SupplierModel.all()

    @classmethod
    def get_by_id(cls, supplier_id: int):
        return SupplierModel.find(supplier_id)

    @classmethod
    def create(cls, tipo_documento: str, identificacion: str, razon_social: str, email: str, telefono: str = "", direccion: str = "", contacto: str = "", status: str = "active"):
        """Crea un nuevo proveedor."""
        tipo_documento = (tipo_documento or "RUC").strip().upper()
        identificacion = (identificacion or "").strip()
        razon_social = (razon_social or "").strip()
        email = (email or "").strip().lower()
        telefono = (telefono or "").strip()
        direccion = (direccion or "").strip()
        contacto = (contacto or "").strip()

        if not identificacion:
            return False, "La identificación / RUC del proveedor es requerida."
        if not razon_social:
            return False, "La razón social o nombre de la empresa proveedora es requerida."
        if not email:
            return False, "El correo electrónico es requerido."

        existing = SupplierModel.where(identificacion=identificacion)
        if existing:
            return False, f"Ya existe un proveedor registrado con la identificación '{identificacion}'."

        new_supplier = SupplierModel.create(
            tipo_documento=tipo_documento,
            identificacion=identificacion,
            razon_social=razon_social,
            email=email,
            telefono=telefono,
            direccion=direccion,
            contacto=contacto,
            status=status if status in ("active", "inactive") else "active"
        )
        return True, new_supplier

    @classmethod
    def update(cls, supplier_id: int, tipo_documento: str, identificacion: str, razon_social: str, email: str, telefono: str = "", direccion: str = "", contacto: str = "", status: str = "active"):
        """Actualiza un proveedor existente."""
        identificacion = (identificacion or "").strip()
        razon_social = (razon_social or "").strip()
        email = (email or "").strip().lower()

        try:
            sid = int(supplier_id)
        except (ValueError, TypeError):
            return False, "ID de proveedor inválido."

        supplier = SupplierModel.find(sid)
        if not supplier:
            return False, "Proveedor no encontrado."

        if not identificacion:
            return False, "La identificación es requerida."
        if not razon_social:
            return False, "La razón social es requerida."

        existing = SupplierModel.where(identificacion=identificacion)
        if existing and int(existing[0]["id"]) != sid:
            return False, f"Ya existe otro proveedor con la identificación '{identificacion}'."

        updated = SupplierModel.update_by_id(
            sid,
            tipo_documento=(tipo_documento or "RUC").strip().upper(),
            identificacion=identificacion,
            razon_social=razon_social,
            email=email,
            telefono=(telefono or "").strip(),
            direccion=(direccion or "").strip(),
            contacto=(contacto or "").strip(),
            status=status if status in ("active", "inactive") else "active"
        )
        return True, updated

    @classmethod
    def delete(cls, supplier_id: int):
        """Elimina un proveedor."""
        supplier = SupplierModel.find(supplier_id)
        if not supplier:
            return False, "Proveedor no encontrado."
        SupplierModel.delete_by_id(supplier_id)
        return True, "Proveedor eliminado exitosamente."
