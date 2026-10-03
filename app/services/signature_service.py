import os
import shutil
from pathlib import Path
from core.logger import get_logger

logger = get_logger("SignatureService")
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class SignatureService:
    @classmethod
    def save_certificate(cls, source_file_path: str, password: str = "") -> tuple:
        """Guarda y valida un certificado de firma electrónica (.p12 / .pfx).
        
        Returns:
            (success: bool, target_path_or_err: str)
        """
        if not source_file_path or not os.path.exists(source_file_path):
            return False, "El archivo de firma electrónica especificado no existe."

        ext = Path(source_file_path).suffix.lower()
        if ext not in ('.p12', '.pfx'):
            return False, "Formato de firma no soportado. Debe ser un archivo .p12 o .pfx"

        certs_dir = BASE_DIR / "assets" / "certs"
        certs_dir.mkdir(parents=True, exist_ok=True)

        filename = f"firma_electronica{ext}"
        target_path = certs_dir / filename

        try:
            shutil.copy2(source_file_path, target_path)
            
            # Optional Cryptography verification if password provided
            if password:
                try:
                    from cryptography.hazmat.primitives.serialization import pkcs12
                    with open(target_path, "rb") as f:
                        p12_data = f.read()
                    private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                        p12_data, password.encode('utf-8')
                    )
                    logger.info("Certificado digital PKCS12 verificado exitosamente con cryptography.")
                except Exception as ve:
                    logger.warning(f"Advertencia al validar contraseña de la firma: {ve}")

            return True, str(target_path)
        except Exception as e:
            logger.error(f"Error al copiar archivo de firma electrónica: {e}")
            return False, f"Error al procesar la firma electrónica: {str(e)}"
