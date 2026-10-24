
from app.models.user_model import UserModel

class LoginController:
    """Controlador de autenticación con SQLite."""

    @classmethod
    def authenticate(cls, email: str, password: str):
        """Verifica las credenciales consultando la base de datos SQLite.

        Returns:
            dict con los datos del usuario si es correcto, None si falla.
        """
        return UserModel.authenticate(email, password)

