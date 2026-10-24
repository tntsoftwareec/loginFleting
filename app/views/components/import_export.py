"""Barra reutilizable de importación/exportación para las vistas del sistema.

Botones:
    Importar Excel · Plantilla · Excel · PDF

El botón "Importar" lee un .xlsx, el de "Plantilla" descarga un Excel vacío con
una hoja de instrucciones, y los botones "Excel"/"PDF" exportan el listado.
"""
import tempfile

import flet as ft
from core import theme as T

from app.views.ui_helpers import (
    close_dialog,
    get_file_picker,
    open_dialog,
    show_toast,
    wide_dialog_width,
)
from core.import_export import (
    KINDS,
    build_export,
    build_template,
    import_file,
    summary_message,
)


def _is_web_or_mobile(page: ft.Page) -> bool:
    try:
        return bool(getattr(page, "web", False)) or bool(page.platform.is_mobile())
    except Exception:  # noqa: BLE001
        return False


def _show_errors(page: ft.Page, result: dict):
    errors = result.get("errors") or []
    if not errors:
        return
    shown = errors[:12]
    dialog = ft.AlertDialog(
        title=ft.Text("Detalle de la importación", color=T.ON_ACCENT, weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column(
                [ft.Text(line, color=T.DANGER_TEXT, size=12, selectable=True) for line in shown]
                + ([ft.Text(f"... y {len(errors) - len(shown)} más", color=T.TEXT_MUTED, size=11)]
                   if len(errors) > len(shown) else []),
                spacing=6, scroll=ft.ScrollMode.AUTO, tight=True,
            ),
            width=wide_dialog_width(page, 560),
        ),
        actions=[ft.TextButton("Cerrar", on_click=lambda e: close_dialog(page, dialog))],
        bgcolor=T.SURFACE_ALT,
    )
    open_dialog(page, dialog)


def _save_bytes(page: ft.Page, picker: ft.FilePicker, filename: str, data: bytes):
    async def run():
        extension = filename.rsplit(".", 1)[-1].lower()
        try:
            path = await picker.save_file(
                dialog_title="Guardar archivo",
                file_name=filename,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=[extension],
                src_bytes=data,
            )
        except Exception as exc:  # noqa: BLE001
            show_toast(page, f"No se pudo guardar el archivo: {exc}", is_error=True)
            return

        if path:
            # En web y móvil el propio cliente (SAF / descarga) escribe los
            # bytes y puede devolver una URI de contenido no escribible, así
            # que no volvemos a abrir la ruta en modo escritura.
            if _is_web_or_mobile(page):
                show_toast(page, "Archivo guardado en el dispositivo.")
                return
            try:
                with open(path, "wb") as fh:
                    fh.write(data)
                show_toast(page, f"Archivo guardado en: {path}")
            except Exception as exc:  # noqa: BLE001
                show_toast(page, f"No se pudo escribir el archivo: {exc}", is_error=True)
        elif getattr(page, "web", False):
            show_toast(page, "Archivo enviado al dispositivo.")
        else:
            show_toast(page, "Guardado cancelado.")

    page.run_task(run)


def build_import_export_bar(page: ft.Page, *, kind: str, on_changed=None) -> ft.Row:
    """Devuelve la fila de botones de importación/exportación para `kind`."""
    meta = KINDS[kind]
    picker = get_file_picker(page)

    def do_import(e=None):
        async def run():
            try:
                files = await picker.pick_files(
                    dialog_title=f"Importar {meta['label']} desde Excel",
                    file_type=ft.FilePickerFileType.CUSTOM,
                    allowed_extensions=["xlsx", "xlsm"],
                    allow_multiple=False,
                    with_data=True,
                )
            except Exception as exc:  # noqa: BLE001
                show_toast(page, f"No se pudo abrir el archivo: {exc}", is_error=True)
                return

            if not files:
                return
            selected = files[0]
            path = selected.path
            if not path and getattr(selected, "bytes", None):
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                tmp.write(selected.bytes)
                tmp.close()
                path = tmp.name

            result = import_file(kind, path)
            show_toast(page, summary_message(result), is_error=bool(result.get("errors")))
            if result.get("errors"):
                _show_errors(page, result)
            if on_changed and (result.get("created") or result.get("updated")):
                on_changed()

        page.run_task(run)

    def do_template(e=None):
        filename, data = build_template(kind)
        _save_bytes(page, picker, filename, data)

    def exporter(fmt):
        def handler(e=None):
            filename, data = build_export(kind, fmt)
            _save_bytes(page, picker, filename, data)
        return handler

    compact = ft.ButtonStyle(
        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
        text_style=ft.TextStyle(size=12),
    )
    return ft.Row(
        controls=[
            ft.TextButton("Importar", icon=ft.Icons.UPLOAD_FILE_ROUNDED,
                          tooltip="Importar desde Excel (.xlsx)",
                          style=compact, on_click=do_import),
            ft.TextButton("Plantilla", icon=ft.Icons.DOWNLOAD_ROUNDED,
                          tooltip="Descargar plantilla de Excel",
                          style=compact, on_click=do_template),
            ft.TextButton("Excel", icon=ft.Icons.TABLE_VIEW_ROUNDED,
                          tooltip="Exportar a Excel",
                          style=compact, on_click=exporter("xlsx")),
            ft.TextButton("PDF", icon=ft.Icons.PICTURE_AS_PDF_ROUNDED,
                          tooltip="Exportar a PDF",
                          style=compact, on_click=exporter("pdf")),
        ],
        spacing=0,
        wrap=True,
        alignment=ft.MainAxisAlignment.END,
    )
