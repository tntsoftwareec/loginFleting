import re
from app.models.client_model import ClientModel

class ClientController:
    @classmethod
    def get_all(cls):
        """Retorna todos los clientes."""
        return ClientModel.all()

    @classmethod
    def get_by_id(cls, client_id: int):
        return ClientModel.find(client_id)

    @classmethod
    def create(cls, tipo_documento: str, identificacion: str, razon_social: str, email: str, telefono: str = "", direccion: str = "", status: str = "active"):
        """Crea un nuevo cliente.
        
        Returns:
            (success: bool, data_or_error: dict|str)
        """
        tipo_documento = (tipo_documento or "CEDULA").strip().upper()
        identificacion = (identificacion or "").strip()
        razon_social = (razon_social or "").strip()
        email = (email or "").strip().lower()
        telefono = (telefono or "").strip()
        direccion = (direccion or "").strip()

        if not identificacion:
            return False, "La identificación (RUC/Cédula/Pasaporte) es requerida."
        if not razon_social:
            return False, "La razón social o nombre completo es requerido."
        if not email:
            return False, "El correo electrónico es requerido."
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            return False, "Formato de correo electrónico inválido."

        existing = ClientModel.where(identificacion=identificacion)
        if existing:
            return False, f"Ya existe un cliente registrado con la identificación '{identificacion}'."

        new_client = ClientModel.create(
            tipo_documento=tipo_documento,
            identificacion=identificacion,
            razon_social=razon_social,
            email=email,
            telefono=telefono,
            direccion=direccion,
            status=status if status in ("active", "inactive") else "active"
        )
        return True, new_client

    @classmethod
    def update(cls, client_id: int, tipo_documento: str, identificacion: str, razon_social: str, email: str, telefono: str = "", direccion: str = "", status: str = "active"):
        """Actualiza un cliente existente."""
        identificacion = (identificacion or "").strip()
        razon_social = (razon_social or "").strip()
        email = (email or "").strip().lower()

        try:
            cid = int(client_id)
        except (ValueError, TypeError):
            return False, "ID de cliente inválido."

        client = ClientModel.find(cid)
        if not client:
            return False, "Cliente no encontrado."

        if not identificacion:
            return False, "La identificación es requerida."
        if not razon_social:
            return False, "La razón social es requerida."
        if not email:
            return False, "El correo electrónico es requerido."

        existing = ClientModel.where(identificacion=identificacion)
        if existing and int(existing[0]["id"]) != cid:
            return False, f"Ya existe otro cliente con la identificación '{identificacion}'."

        updated = ClientModel.update_by_id(
            cid,
            tipo_documento=(tipo_documento or "CEDULA").strip().upper(),
            identificacion=identificacion,
            razon_social=razon_social,
            email=email,
            telefono=(telefono or "").strip(),
            direccion=(direccion or "").strip(),
            status=status if status in ("active", "inactive") else "active"
        )
        return True, updated

    @classmethod
    def delete(cls, client_id: int):
        """Elimina un cliente."""
        client = ClientModel.find(client_id)
        if not client:
            return False, "Cliente no encontrado."
        ClientModel.delete_by_id(client_id)
        return True, "Cliente eliminado exitosamente."
