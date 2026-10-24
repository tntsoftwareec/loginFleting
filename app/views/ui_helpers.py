"""Utilidades de interfaz compartidas por las vistas del sistema.

Centraliza toasts, diálogos, botones y decisiones de layout responsive para
que todas las vistas se comporten igual en escritorio y en móvil.
"""
import os
import subprocess
import sys

import flet as ft
from core import theme as T

from core.responsive import MOBILE_BREAKPOINT, get_dialog_width, is_mobile
from core.state import AppState


def open_dialog(page: ft.Page, dialog):
    """Muestra un diálogo usando ``page.show_dialog`` con respaldo en overlay."""
    if hasattr(page, "show_dialog"):
        try:
            page.show_dialog(dialog)
            return
        except Exception:  # noqa: BLE001
            pass
    page.overlay.append(dialog)
    dialog.open = True
    page.update()


def show_toast(page: ft.Page, message: str, is_error: bool = False):
    """Muestra un aviso flotante (funciona en Flet 1.x y 0.86+)."""
    snack = ft.SnackBar(
        content=ft.Text(message, color=T.ON_ACCENT),
        bgcolor=T.DANGER if is_error else T.SUCCESS,
        duration=3500,
        open=True,
    )
    open_dialog(page, snack)


def close_dialog(page: ft.Page, dialog):
    dialog.open = False
    if hasattr(page, "pop_dialog"):
        try:
            page.pop_dialog()
            return
        except Exception:  # noqa: BLE001
            pass
    if dialog in page.overlay:
        page.overlay.remove(dialog)
    page.update()


def is_mobile_page(page: ft.Page) -> bool:
    """True cuando la vista debe renderizarse en modo móvil (tarjetas)."""
    width = getattr(page, "width", None)
    if width:
        return width < MOBILE_BREAKPOINT
    return AppState.device == "mobile"


_SHARES = {}
_PICKERS = {}
_URL_LAUNCHERS = {}


def get_file_picker(page: ft.Page) -> ft.FilePicker:
    """Devuelve un ``ft.FilePicker`` registrado una sola vez por página.

    En Flet 1.x ``FilePicker`` es un servicio (no un control de overlay) y
    ``pick_files``/``save_file`` son corrutinas, así que debe registrarse en
    ``page.services`` y usarse con ``await`` dentro de ``page.run_task``.
    """
    key = id(page)
    picker = _PICKERS.get(key)
    if picker is None:
        picker = ft.FilePicker()
        _PICKERS[key] = picker
        try:
            page.services.append(picker)
        except Exception:  # noqa: BLE001
            pass
    return picker

_MIME_TYPES = {
    "pdf": "application/pdf",
    "xml": "application/xml",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xls": "application/vnd.ms-excel",
    "csv": "text/csv",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
}


def _share_service(page: ft.Page):
    """Devuelve un ``ft.Share`` registrado una sola vez por página."""
    key = id(page)
    share = _SHARES.get(key)
    if share is None:
        share = ft.Share()
        _SHARES[key] = share
        try:
            page.services.append(share)
        except Exception:  # noqa: BLE001
            pass
    return share


def _is_mobile_platform(page: ft.Page) -> bool:
    try:
        return bool(page.platform.is_mobile())
    except Exception:  # noqa: BLE001
        return sys.platform in ("android", "ios")


def is_mobile_platform(page: ft.Page) -> bool:
    """True cuando la app corre en Android/iOS (no solo layout compacto)."""
    return _is_mobile_platform(page)


def _url_launcher(page: ft.Page) -> ft.UrlLauncher:
    """Devuelve un ``UrlLauncher`` registrado una sola vez por página."""
    key = id(page)
    launcher = _URL_LAUNCHERS.get(key)
    if launcher is None:
        launcher = ft.UrlLauncher()
        _URL_LAUNCHERS[key] = launcher
        try:
            page.services.append(launcher)
        except Exception:  # noqa: BLE001
            pass
    return launcher


def open_url(page: ft.Page, url: str):
    """Abre un enlace externo sin bloquear el hilo de UI."""
    async def run():
        try:
            await _url_launcher(page).launch_url(url)
        except Exception as exc:  # noqa: BLE001
            show_toast(page, f"No se pudo abrir el enlace: {exc}", is_error=True)

    page.run_task(run)


def share_file(
    page: ft.Page,
    path: str,
    *,
    text: str = "",
    title: str = "Compartir documento",
    mime_type: str | None = None,
    on_result=None,
) -> bool:
    """Comparte un archivo con la hoja nativa del sistema.

    En Android/iOS permite elegir WhatsApp y envía el archivo adjunto. En
    escritorio se intenta la hoja nativa; si no está disponible, ``on_result``
    recibe ``None`` para que la vista pueda usar un respaldo.
    """
    if not path or not os.path.isfile(path):
        show_toast(page, "El archivo no existe en disco.", is_error=True)
        if on_result:
            on_result(None)
        return False

    extension = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    mime = mime_type or _MIME_TYPES.get(extension, "application/octet-stream")

    async def run():
        result = None
        try:
            result = await _share_service(page).share_files(
                [
                    ft.ShareFile(
                        path=path,
                        mime_type=mime,
                        name=os.path.basename(path),
                    )
                ],
                title=title,
                text=text or None,
            )
        except Exception as exc:  # noqa: BLE001
            show_toast(
                page,
                f"No se pudo abrir el menú para compartir: {exc}",
                is_error=True,
            )
        if on_result:
            on_result(result)

    page.run_task(run)
    return True


def reveal_in_file_manager(page: ft.Page, path: str) -> bool:
    """Abre la carpeta del archivo en el explorador (escritorio)."""
    if not path or not os.path.isfile(path):
        show_toast(page, "El archivo no existe en disco.", is_error=True)
        return False
    try:
        if sys.platform.startswith("win"):
            subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", path])
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(path)])
        return True
    except Exception as exc:  # noqa: BLE001
        show_toast(page, f"No se pudo abrir la carpeta: {exc}", is_error=True)
        return False


def send_whatsapp_document(
    page: ft.Page,
    *,
    link: str,
    pdf_path: str,
    message: str,
    on_sent=None,
) -> bool:
    """Comparte el PDF de una cotización para enviarlo por WhatsApp.

    Primero intenta la hoja nativa de compartir (el PDF va adjunto). Si no
    está disponible, abre WhatsApp con el mensaje preparado y, en escritorio,
    muestra la carpeta del PDF para arrastrarlo al chat.
    """
    if not pdf_path or not os.path.isfile(pdf_path):
        show_toast(page, "No se encontró el PDF de la cotización.", is_error=True)
        return False

    def finish_fallback():
        open_url(page, link)
        if not _is_mobile_platform(page):
            reveal_in_file_manager(page, pdf_path)
            show_toast(
                page,
                "WhatsApp abierto con el mensaje. Adjunta el PDF desde la "
                "carpeta que se abrió.",
            )
        else:
            show_toast(
                page,
                "WhatsApp abierto con el mensaje. Adjunta el PDF desde el chat.",
            )
        if on_sent:
            on_sent()

    def handle_result(result):
        status = getattr(result, "status", None)
        if result is not None and status == ft.ShareResultStatus.SUCCESS:
            show_toast(page, "PDF compartido. Selecciona WhatsApp para enviarlo.")
            if on_sent:
                on_sent()
            return
        if result is not None and status == ft.ShareResultStatus.DISMISSED:
            return
        # None (error/plataforma sin soporte) o UNAVAILABLE.
        finish_fallback()

    share_file(
        page,
        pdf_path,
        text=message,
        title="Compartir cotización por WhatsApp",
        mime_type="application/pdf",
        on_result=handle_result,
    )
    return True


def open_path(page: ft.Page, path: str) -> bool:
    """Abre un archivo local.

    En escritorio usa el visor predeterminado del sistema. En Android/iOS
    ``xdg-open`` no existe y el archivo vive en almacenamiento privado de la
    app, así que se usa la hoja de compartir del sistema (el usuario puede
    abrirlo con su visor de PDF, enviarlo, etc.).
    """
    if not path or not os.path.isfile(path):
        show_toast(page, "El archivo no existe en disco.", is_error=True)
        return False

    if _is_mobile_platform(page):
        extension = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        mime = _MIME_TYPES.get(extension, "application/octet-stream")

        async def share():
            try:
                await _share_service(page).share_files(
                    [ft.ShareFile(path=path, mime_type=mime)],
                    title="Abrir documento",
                )
            except Exception as exc:  # noqa: BLE001
                show_toast(
                    page, f"No se pudo abrir el archivo: {exc}", is_error=True
                )

        page.run_task(share)
        return True

    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception as exc:  # noqa: BLE001
        show_toast(page, f"No se pudo abrir el archivo: {exc}", is_error=True)
        return False


def open_manual_service_dialog(page: ft.Page, on_add):
    """Diálogo para agregar una línea de servicio no registrada en el catálogo.

    ``on_add`` recibe un ítem compatible con el carrito del POS y de
    cotizaciones: ``tipo="servicio"``, ``id=None`` y los datos de facturación.
    """
    tf_codigo = ft.TextField(label="Código", value="SERV", expand=True)
    tf_nombre = ft.TextField(
        label="Descripción del servicio",
        hint_text="Ej: Soporte técnico remoto",
        expand=True,
    )
    tf_precio = ft.TextField(label="Precio unitario ($)", value="0.00", expand=True)
    tf_cantidad = ft.TextField(label="Cantidad", value="1", expand=True)
    dd_iva = ft.Dropdown(
        label="Tarifa IVA",
        value="15",
        options=[
            ft.dropdown.Option("15", "IVA 15%"),
            ft.dropdown.Option("0", "IVA 0%"),
        ],
        expand=True,
    )
    tf_desc = ft.TextField(
        label="Detalle adicional (opcional)",
        multiline=True,
        max_lines=2,
        expand=True,
    )

    def save(e):
        nombre = (tf_nombre.value or "").strip()
        codigo = (tf_codigo.value or "").strip().upper() or "SERV"
        try:
            precio = float((tf_precio.value or "0").replace(",", "."))
            cantidad = float((tf_cantidad.value or "1").replace(",", "."))
            iva = float(dd_iva.value or "15")
        except (TypeError, ValueError):
            show_toast(page, "Precio, cantidad o IVA inválidos.", is_error=True)
            return

        if not nombre:
            show_toast(page, "Escribe la descripción del servicio.", is_error=True)
            return
        if precio < 0:
            show_toast(page, "El precio no puede ser negativo.", is_error=True)
            return
        if cantidad <= 0:
            show_toast(page, "La cantidad debe ser mayor a cero.", is_error=True)
            return

        detalle = (tf_desc.value or "").strip()
        item = {
            "id": None,
            "tipo": "servicio",
            "codigo": codigo,
            # El detalle forma parte de la descripción que se imprime en el
            # PDF y se envía en el XML, porque el modelo solo guarda ``nombre``.
            "nombre": f"{nombre} - {detalle}" if detalle else nombre,
            "precio": precio,
            "cantidad": cantidad,
            "descuento": 0.0,
            "iva_porcentaje": iva,
        }
        close_dialog(page, dlg)
        on_add(item)

    dlg = ft.AlertDialog(
        title=ft.Text("Agregar servicio manual", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row([tf_codigo, tf_cantidad], spacing=10),
                    tf_nombre,
                    ft.Row([tf_precio, dd_iva], spacing=10),
                    tf_desc,
                ],
                tight=True,
                spacing=12,
            ),
            width=form_dialog_width(page, 520),
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: close_dialog(page, dlg)),
            ft.FilledButton(
                "Agregar al carrito",
                icon=ft.Icons.ADD_SHOPPING_CART_ROUNDED,
                style=ft.ButtonStyle(bgcolor=T.PRIMARY, color=T.ON_ACCENT),
                on_click=save,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    open_dialog(page, dlg)


def wide_dialog_width(page: ft.Page, preferred: int = 900) -> int:
    """Ancho para diálogos grandes (carrito, configuración)."""
    width = getattr(page, "width", None) or 1280
    if is_mobile(width):
        return int(max(280, width - 40))
    return int(min(preferred, max(420, width - 120)))


def form_dialog_width(page: ft.Page, preferred: int = 500) -> int:
    """Ancho para diálogos de formulario (crear/editar)."""
    return get_dialog_width(page, preferred)


def primary_button(label: str, on_click, icon=None, bgcolor: str | None = None, expand: bool = False):
    bgcolor = bgcolor or T.PRIMARY
    btn_cls = getattr(ft, "FilledButton", getattr(ft, "ElevatedButton", ft.TextButton))
    content = ft.Row(
        [ft.Icon(icon, size=18), ft.Text(label, weight=ft.FontWeight.BOLD)],
        spacing=8,
        alignment=ft.MainAxisAlignment.CENTER,
    ) if icon else ft.Text(label, weight=ft.FontWeight.BOLD)
    return btn_cls(
        content=content,
        style=ft.ButtonStyle(color=T.ON_ACCENT, bgcolor=bgcolor, padding=14,
                             shape=ft.RoundedRectangleBorder(radius=8)),
        on_click=on_click,
        expand=expand,
    )


def field(label: str, value="", **kwargs):
    return ft.TextField(label=label, value=value, expand=True, **kwargs)


def section_title(text: str):
    return ft.Text(text, color=T.TEXT, size=13, weight=ft.FontWeight.BOLD)


def chip(text: str, bgcolor: str | None = None, color: str | None = None):
    bgcolor = bgcolor or T.CHIP_BG
    color = color or T.SUCCESS_TEXT
    return ft.Container(
        content=ft.Text(text, color=color, size=10, weight=ft.FontWeight.W_600),
        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
        border_radius=10,
        bgcolor=bgcolor,
    )


def stat_card(title: str, value: str, icon, color: str, subtitle: str = "") -> ft.Container:
    """Tarjeta de resumen reutilizable (nº de facturas, total facturado, etc.)."""
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(icon, color=color, size=22),
                    bgcolor=color + "22",
                    border_radius=10,
                    padding=10,
                ),
                ft.Column(
                    controls=[
                        ft.Text(title, color=T.TEXT_MUTED, size=11, weight=ft.FontWeight.W_500),
                        ft.Text(value, color=T.TEXT, size=19, weight=ft.FontWeight.BOLD),
                        ft.Text(subtitle, color=T.TEXT_SUBTLE, size=10),
                    ],
                    spacing=1,
                    tight=True,
                ),
            ],
            spacing=12,
        ),
        padding=14,
        bgcolor=T.SURFACE,
        border_radius=12,
        border=T.border(),
        col={"xs": 12, "sm": 6, "md": 3},
    )
