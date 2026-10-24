import os
import shutil
from pathlib import Path
from core.logger import get_logger
from core.paths import GENERATED_DIR

logger = get_logger("SignatureService")

class SignatureService:
    @classmethod
    def save_certificate(cls, source_file_path: str, password: str = "") -> tuple:
        """Guarda y valida un certificado de firma electrónica (.p12 / .pfx).

        Returns:
            (success: bool, target_path_or_err: str)
        """
        # Normaliza rutas escritas a mano (comillas, "~", prefijo file://).
        path = (source_file_path or "").strip().strip('"').strip("'")
        if path.startswith("file://"):
            path = path[7:]
        path = os.path.expanduser(path)

        if not path or not os.path.isfile(path):
            return False, "El archivo de firma electrónica especificado no existe."

        ext = Path(path).suffix.lower()
        if ext not in ('.p12', '.pfx'):
            return False, "Formato de firma no soportado. Debe ser un archivo .p12 o .pfx"

        try:
            with open(path, "rb") as fh:
                p12_data = fh.read()
        except OSError as e:
            logger.error(f"No se pudo leer el certificado {path}: {e}")
            return False, f"No se pudo leer el archivo de firma: {e}"

        # Validamos el certificado y su contraseña ANTES de guardarlo. Así no
        # se registra una firma inservible (contraseña incorrecta o .p12 roto).
        if password:
            try:
                from cryptography.hazmat.primitives.serialization import pkcs12

                private_key, certificate, _ = pkcs12.load_key_and_certificates(
                    p12_data, password.encode("utf-8")
                )
                if private_key is None or certificate is None:
                    return False, (
                        "El archivo .p12 no contiene una clave privada y un "
                        "certificado válidos."
                    )
                logger.info("Certificado digital PKCS12 verificado exitosamente.")
            except Exception as ve:
                logger.warning(f"No se pudo validar la contraseña de la firma: {ve}")
                return False, (
                    "No se pudo validar la firma electrónica. Verifica que la "
                    "contraseña sea correcta y que el archivo .p12/.pfx sea válido."
                )

        certs_dir = GENERATED_DIR / "certs"
        certs_dir.mkdir(parents=True, exist_ok=True)

        filename = f"firma_electronica{ext}"
        target_path = certs_dir / filename

        try:
            shutil.copy2(path, target_path)
            return True, str(target_path)
        except OSError as e:
            logger.error(f"Error al copiar archivo de firma electrónica: {e}")
            return False, f"Error al procesar la firma electrónica: {str(e)}"
