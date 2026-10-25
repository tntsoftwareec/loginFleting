from core.base_model import BaseModel

class CompanyModel(BaseModel):
    table_name = "company"

    @classmethod
    def get_info(cls):
        info = cls.first()
        if not info:
            info = cls.create(
                ruc="",
                razon_social="MI EMPRESA",
                nombre_comercial="MI NEGOCIO",
                direccion_matriz="",
                direccion_establecimiento="",
                agente_retencion="",
                telefono="",
                email="",
                ambiente_sri=1,
                establecimiento="001",
                punto_emision="001",
                secuencial_factura=1,
                secuencial_cotizacion=1,
                contribuyente_especial="",
                obligado_contabilidad="NO"
            )
        return info
