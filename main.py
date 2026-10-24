
import flet as ft
from configs.app_config import AppConfig
from core.logger import get_logger
from core.error_handler import GlobalErrorHandler
from core.responsive import get_device_type
from core.state import AppState

logger = get_logger("App")


def main(page: ft.Page):
    try:
        page.assets_dir = "assets"
        page.title = AppConfig.APP_NAME

        # Preferencias persistentes (tema e idioma).
        from core import preferences, theme

        prefs = preferences.load()
        AppState.language = prefs.get("language", AppState.language)
        AppState.theme_mode = prefs.get("theme_mode", AppConfig.DEFAULT_THEME_MODE)

        # Paleta adaptable: aplica el tema guardado (o el del sistema).
        theme.apply(page, AppState.theme_mode)

        if page.platform in (ft.PagePlatform.WINDOWS, ft.PagePlatform.LINUX, ft.PagePlatform.MACOS):
            page.window.width = AppConfig.DEFAULT_SCREEN["width"]
            page.window.height = AppConfig.DEFAULT_SCREEN["height"]

        from core.i18n import I18n
        I18n.load(AppState.language)

        from core.router import Router
        router = Router(page)

        # ── Detección de dispositivo (móvil / tablet / escritorio) ──────────
        # Se calcula al iniciar y se recalcula cuando cambia la categoría,
        # re-renderizando la vista para aplicar el layout correspondiente.
        def on_resize(e=None):
            if not page.width:
                return

            new_device = get_device_type(page.width)
            # Primer cálculo: solo inicializa, no re-renderiza (aún no hay ruta).
            if AppState.device is None:
                AppState.device = new_device
                return
            # Cambio de categoría (móvil/tablet/escritorio): re-renderiza.
            if new_device != AppState.device:
                AppState.device = new_device
                router.rerender()

        page.on_resize = on_resize
        on_resize()

        # Si el usuario eligió "Sistema", seguimos los cambios de brillo del SO.
        def on_brightness_change(e=None):
            if AppState.theme_mode != theme.SYSTEM:
                return
            theme.apply(page)
            router.rerender()

        page.on_platform_brightness_change = on_brightness_change

        # El guard de autenticación del Router redirige a /login si no hay sesión.
        router.navigate("/login")

        logger.info("App iniciada con exito")

    except Exception as e:
        GlobalErrorHandler.handle(page, e)


ft.run(main)
