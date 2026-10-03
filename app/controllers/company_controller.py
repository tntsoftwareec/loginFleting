from app.models.company_model import CompanyModel
from app.services.signature_service import SignatureService

class CompanyController:
    @classmethod
    def get_info(cls):
        """Retorna los datos de la empresa."""
        return CompanyModel.get_info()

    @classmethod
    def update_info(cls, ruc: str, razon_social: str, nombre_comercial: str, direccion_matriz: str, telefono: str, email: str, ambiente_sri: int = 1, establecimiento: str = "001", punto_emision: str = "001", contribuyente_especial: str = "", obligado_contabilidad: str = "NO", sri_email: str = "recepcion.sri@sri.gob.ec", smtp_host: str = "smtp.gmail.com", smtp_port: int = 587, smtp_user: str = "", smtp_pass: str = "", smtp_ssl: bool = False):
        """Actualiza los datos del negocio/empresa."""
        company = cls.get_info()

        ruc = (ruc or "").strip()
        razon_social = (razon_social or "").strip()

        if not ruc or len(ruc) < 13:
            return False, "El RUC de la empresa debe tener 13 dígitos."
        if not razon_social:
            return False, "La razón social de la empresa es requerida."

        updated = CompanyModel.update_by_id(
            company["id"],
            ruc=ruc,
            razon_social=razon_social,
            nombre_comercial=(nombre_comercial or "").strip(),
            direccion_matriz=(direccion_matriz or "").strip(),
            telefono=(telefono or "").strip(),
            email=(email or "").strip(),
            ambiente_sri=int(ambiente_sri),
            establecimiento=(establecimiento or "001").strip(),
            punto_emision=(punto_emision or "001").strip(),
            contribuyente_especial=(contribuyente_especial or "").strip(),
            obligado_contabilidad="SI" if str(obligado_contabilidad).upper() == "SI" else "NO",
            sri_email=(sri_email or "").strip(),
            smtp_host=(smtp_host or "smtp.gmail.com").strip(),
            smtp_port=int(smtp_port) if smtp_port else 587,
            smtp_user=(smtp_user or "").strip(),
            smtp_pass=smtp_pass if smtp_pass is not None else company.get("smtp_pass", ""),
            smtp_ssl=1 if smtp_ssl else 0
        )
        return True, updated

    @classmethod
    def upload_signature(cls, source_file_path: str, signature_password: str = ""):
        """Sube y registra la firma electrónica de la empresa."""
        company = cls.get_info()

        success, res = SignatureService.save_certificate(source_file_path, signature_password)
        if not success:
            return False, res

        updated = CompanyModel.update_by_id(
            company["id"],
            firma_path=res,
            firma_pass=signature_password
        )
        return True, f"Firma electrónica guardada exitosamente en: {res}"
