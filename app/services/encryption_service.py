"""
EncryptionService — symmetric encryption for sensitive fields (e.g. smtp_pass).

Uses Fernet (AES-128-CBC + HMAC) with a key derived from SECRET_KEY
via PBKDF2HMAC-SHA256 (100k iterations, fixed salt).
"""
import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.logger import get_logger
from core.paths import DATA_DIR

logger = get_logger("EncryptionService")

# Fixed salt — deterministic key derivation so the same SECRET_KEY
# always produces the same encryption key across restarts.
_SALT = b"fleting_smtp_encryption_salt_v1"

# Clave local generada automáticamente cuando no existe la variable de
# entorno. Se guarda junto a la base de datos, en el directorio persistente.
_KEY_FILE = DATA_DIR / "data" / ".secret_key"


def generate_secret_key() -> str:
    """Genera una clave secreta nueva y segura para FLETING_SECRET_KEY."""
    return Fernet.generate_key().decode("utf-8")


def _load_or_create_key() -> str:
    """Devuelve la clave secreta, generando una persistente si es necesario.

    Orden de prioridad:
    1. Variable de entorno ``FLETING_SECRET_KEY`` (útil en servidores).
    2. Archivo local ``data/.secret_key``.
    3. Si no existe ninguno, se genera y se guarda automáticamente.

    Así la app funciona sin configuración manual y mantiene la misma clave
    entre reinicios/actualizaciones.
    """
    env_key = os.environ.get("FLETING_SECRET_KEY", "").strip()
    if env_key:
        return env_key

    try:
        if _KEY_FILE.is_file():
            key = _KEY_FILE.read_text(encoding="utf-8").strip()
            if key:
                return key

        key = generate_secret_key()
        _KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        _KEY_FILE.write_text(key, encoding="utf-8")
        try:
            os.chmod(_KEY_FILE, 0o600)
        except OSError:
            pass
        logger.info("Clave de cifrado local generada en %s", _KEY_FILE)
        return key
    except OSError as exc:
        raise RuntimeError(
            "No se pudo crear la clave de cifrado local en "
            f"{_KEY_FILE}. Verifica los permisos del directorio de datos."
        ) from exc


def _get_secret_key() -> str:
    """Return the application secret key (environment or local file)."""
    return _load_or_create_key()


def _derive_fernet_key(secret_key: str) -> bytes:
    """Derive a Fernet-compatible 32-byte key from SECRET_KEY using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=100_000,
    )
    derived = kdf.derive(secret_key.encode("utf-8"))
    return base64.urlsafe_b64encode(derived)


class EncryptionService:
    """Encrypt and decrypt sensitive string values."""

    _fernet = None

    @classmethod
    def _get_fernet(cls) -> Fernet:
        if cls._fernet is None:
            key = _derive_fernet_key(_get_secret_key())
            cls._fernet = Fernet(key)
        return cls._fernet

    # ── Public API ──────────────────────────────────────────────────────────

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        Encrypt a plaintext string and return a base64-encoded ciphertext.

        Returns the original value unchanged if empty or None.
        """
        if not plaintext:
            return ""
        try:
            f = cls._get_fernet()
            token = f.encrypt(plaintext.encode("utf-8"))
            return token.decode("utf-8")
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """
        Decrypt a base64-encoded ciphertext back to plaintext.

        Returns an empty string if input is empty or None.
        Logs a warning and returns empty string if decryption fails
        (e.g. wrong SECRET_KEY or corrupted data).
        """
        if not ciphertext:
            return ""
        try:
            f = cls._get_fernet()
            plaintext = f.decrypt(ciphertext.encode("utf-8"))
            return plaintext.decode("utf-8")
        except InvalidToken:
            logger.warning(
                "Decryption failed — InvalidToken. "
                "Data may have been encrypted with a different SECRET_KEY."
            )
            return ""
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return ""
