import os
import uuid
from pathlib import Path

from app.models.company_model import CompanyModel
from app.services.signature_service import SignatureService
from app.services.encryption_service import EncryptionService
from core.paths import GENERATED_DIR

COMPANY_ASSETS_DIR = GENERATED_DIR / "company"
ALLOWED_LOGO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _clean_source_path(source: str) -> str:
    """Normaliza una ruta elegida a mano o por el FilePicker."""
    path = (source or "").strip().strip('"').strip("'")
    if path.startswith("file://"):
        path = path[7:]
    return os.path.expanduser(path)


def _remove_company_logo(logo_path: str):
    """Elimina un logo anterior solo si pertenece al directorio de la empresa."""
    path = _clean_source_path(logo_path)
    if not path:
        return
    try:
        target = Path(path).resolve()
        assets_dir = COMPANY_ASSETS_DIR.resolve()
        if target.is_file() and target.is_relative_to(assets_dir):
            target.unlink()
    except (OSError, ValueError):
        pass


class CompanyController:
    @classmethod
    def get_info(cls):
        """Retorna los datos de la empresa (con smtp_pass desencriptado)."""
        info = CompanyModel.get_info()
        if info and info.get("smtp_pass"):
            info["smtp_pass"] = EncryptionService.decrypt(info["smtp_pass"])
        return info

    @classmethod
    def upload_logo(cls, source_file_path: str):
        """Copia y optimiza el logo de la empresa para usarlo en los PDF."""
        path = _clean_source_path(source_file_path)
        if not path:
            return False, "No se seleccionó ningún archivo de logo."
        if not os.path.isfile(path):
            return False, "El archivo de logo seleccionado no existe."

        extension = Path(path).suffix.lower()
        if extension not in ALLOWED_LOGO_EXTENSIONS:
            return False, "Formato de logo no soportado. Usa JPG, PNG o WEBP."

        try:
            from PIL import Image as PILImage

            target = None
            with PILImage.open(path) as image:
                image.load()
                image_format = (image.format or "").upper()
                if image_format not in ("JPEG", "JPG", "PNG", "WEBP"):
                    return False, "El archivo seleccionado no es una imagen válida."

                image.thumbnail((1200, 1200), PILImage.Resampling.LANCZOS)
                has_alpha = (
                    image.mode in ("RGBA", "LA")
                    or "transparency" in image.info
                )
                target_extension = ".png" if has_alpha else ".jpg"

                COMPANY_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
                filename = f"company_logo_{uuid.uuid4().hex[:12]}{target_extension}"
                target = COMPANY_ASSETS_DIR / filename

                if has_alpha:
                    image.convert("RGBA").save(
                        target,
                        format="PNG",
                        optimize=True,
                    )
                else:
                    image.convert("RGB").save(
                        target,
                        format="JPEG",
                        quality=92,
                        optimize=True,
                    )
        except Exception as exc:  # noqa: BLE001
            if target is not None:
                _remove_company_logo(str(target))
            return False, f"No se pudo procesar el logo: {exc}"

        company = cls.get_info()
        if not company or not company.get("id"):
            _remove_company_logo(str(target))
            return False, "No se encontró la configuración de la empresa."

        old_logo = company.get("logo_path") or ""
        try:
            CompanyModel.update_by_id(company["id"], logo_path=str(target))
        except Exception as exc:  # noqa: BLE001
            _remove_company_logo(str(target))
            return False, f"No se pudo guardar el logo: {exc}"

        if old_logo:
            _remove_company_logo(old_logo)
        return True, "Logo de la empresa actualizado correctamente."

    @classmethod
    def remove_logo(cls):
        """Elimina el logo personalizado y vuelve al logo predeterminado."""
        company = cls.get_info()
        if not company or not company.get("id"):
            return False, "No se encontró la configuración de la empresa."

        old_logo = company.get("logo_path") or ""
        if not old_logo:
            return True, "No hay un logo personalizado configurado."

        try:
            CompanyModel.update_by_id(company["id"], logo_path="")
        except Exception as exc:  # noqa: BLE001
            return False, f"No se pudo quitar el logo: {exc}"

        _remove_company_logo(old_logo)
        return True, "Logo personalizado eliminado. Se usará el logo predeterminado."

    @classmethod
    def update_info(cls, ruc: str, razon_social: str, nombre_comercial: str, direccion_matriz: str, telefono: str, email: str, ambiente_sri: int = 1, establecimiento: str = "001", punto_emision: str = "001", contribuyente_especial: str = "", obligado_contabilidad: str = "NO", sri_email: str = "recepcion.sri@sri.gob.ec", smtp_host: str = "smtp.gmail.com", smtp_port: int = 587, smtp_user: str = "", smtp_pass: str = "", smtp_ssl: bool = False, secuencial_factura: int = 1, secuencial_cotizacion: int = 1, direccion_establecimiento: str = "", agente_retencion: str = ""):
        """Actualiza los datos del negocio/empresa (smtp_pass se encripta antes de guardar)."""
        company = cls.get_info()

        ruc = (ruc or "").strip()
        razon_social = (razon_social or "").strip()

        if not ruc or len(ruc) < 13:
            return False, "El RUC de la empresa debe tener 13 dígitos."
        if not razon_social:
            return False, "La razón social de la empresa es requerida."

        try:
            sec_factura = int(secuencial_factura)
            sec_cotizacion = int(secuencial_cotizacion)
        except (TypeError, ValueError):
            return False, "Los números de factura y cotización deben ser valores numéricos."
        if not (1 <= sec_factura <= 999_999_999):
            return False, "El número inicial de factura debe estar entre 1 y 999999999."
        if not (1 <= sec_cotizacion <= 999_999_999):
            return False, "El número inicial de cotización debe estar entre 1 y 999999999."

        # Encrypt smtp_pass before storing
        encrypted_smtp_pass = ""
        if smtp_pass:
            encrypted_smtp_pass = EncryptionService.encrypt(smtp_pass)
        else:
            # Keep existing encrypted value if no new password provided
            encrypted_smtp_pass = company.get("smtp_pass", "")

        updated = CompanyModel.update_by_id(
            company["id"],
            ruc=ruc,
            razon_social=razon_social,
            nombre_comercial=(nombre_comercial or "").strip(),
            direccion_matriz=(direccion_matriz or "").strip(),
            direccion_establecimiento=(direccion_establecimiento or "").strip(),
            agente_retencion=(agente_retencion or "").strip(),
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
            smtp_pass=encrypted_smtp_pass,
            smtp_ssl=1 if smtp_ssl else 0,
            secuencial_factura=sec_factura,
            secuencial_cotizacion=sec_cotizacion,
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
