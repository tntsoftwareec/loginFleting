from core.base_model import BaseModel

class CompanyModel(BaseModel):
    table_name = "company"

    @classmethod
    def get_info(cls):
        info = cls.first()
        if not info:
            info = cls.create(
                ruc="1792998877001",
                razon_social="FLETING SOLUTIONS S.A.S.",
                nombre_comercial="FLETING POS & TECH",
                direccion_matriz="Av. de los Granados N40-100 y 6 de Diciembre, Quito",
                telefono="0991234567",
                email="facturacion@fleting.ec",
                ambiente_sri=1,
                establecimiento="001",
                punto_emision="001",
                secuencial_factura=1,
                contribuyente_especial="",
                obligado_contabilidad="SI"
            )
        return info
