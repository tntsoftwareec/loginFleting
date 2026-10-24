
# configs/app_config.py

class ScreenConfig:
    MOBILE = {
        "width": 390,
        "height": 758,
        "max_content_width": 390,
    }

    TABLET = {
        "width": 768,
        "height": 1024,
        "max_content_width": 768,
    }

    DESKTOP = {
        "width": 1280,
        "height": 800,
        "max_content_width": None,  # no limit
    }

class AppConfig:
    APP_NAME = "TntPos"
    DEFAULT_SCREEN = ScreenConfig.MOBILE
    # Tema inicial cuando el usuario aún no ha guardado una preferencia:
    # "light", "dark" o "system" (sigue el brillo del sistema operativo).
    DEFAULT_THEME_MODE = "system"
