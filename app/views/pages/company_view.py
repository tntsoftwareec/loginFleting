import os
import tempfile

import flet as ft
from core import theme as T
from app.views.layouts.main_layout import MainLayout
from app.views.ui_helpers import get_file_picker
from app.controllers.company_controller import CompanyController
from core.state import AppState

def _all_border(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)

class CompanyView:
    def __init__(self, page: ft.Page, router):
        self.page = page
        self.router = router
        self.company_info = {}

    def render(self):
        if not AppState.has_permission("can_read", "company"):
            content_layout = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.LOCK_OUTLINED, color=T.DANGER, size=64),
                        ft.Text("Acceso Restringido", color=T.TEXT, size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("No tienes permisos suficientes para acceder a este módulo.", color=T.TEXT_MUTED, size=14),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12,
                ),
                padding=60,
                alignment=ft.Alignment(0, 0),
                expand=True,
            )
            return MainLayout(page=self.page, content=content_layout, router=self.router)

        def show_toast(message: str, is_error: bool = False):
            snack = ft.SnackBar(
                content=ft.Text(message, color=T.ON_ACCENT),
                bgcolor=T.DANGER if is_error else T.SUCCESS,
                duration=3500,
            )
            if hasattr(self.page, "show_dialog"):
                self.page.show_dialog(snack)
            else:
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()

        self.company_info = CompanyController.get_info()

        # Form Fields - General Info
        tf_ruc = ft.TextField(label="R.U.C. Empresa", value=self.company_info.get("ruc", ""), expand=True)
        tf_razon = ft.TextField(label="Razón Social", value=self.company_info.get("razon_social", "MI EMPRESA"), expand=True)
        tf_comercial = ft.TextField(label="Nombre Comercial", value=self.company_info.get("nombre_comercial", "MI NEGOCIO"), expand=True)
        tf_matriz = ft.TextField(label="Dirección Matriz", value=self.company_info.get("direccion_matriz", ""), multiline=True, max_lines=2, expand=True)
        tf_dir_estab = ft.TextField(
            label="Dirección del Establecimiento (opcional)",
            value=self.company_info.get("direccion_establecimiento", ""),
            hint_text="Si se deja vacía se usa la dirección matriz",
            multiline=True,
            max_lines=2,
            expand=True,
        )
        tf_agente = ft.TextField(
            label="N° de Agente de Retención (opcional)",
            value=self.company_info.get("agente_retencion", ""),
            hint_text="Número de resolución del SRI",
            expand=True,
        )
        tf_tel = ft.TextField(label="Teléfono Contacto", value=self.company_info.get("telefono", ""), expand=True)
        tf_email = ft.TextField(label="Email de la Empresa", value=self.company_info.get("email", ""), expand=True)

        # SRI Config
        dd_ambiente = ft.Dropdown(
            label="Ambiente SRI",
            value=str(self.company_info.get("ambiente_sri", 1)),
            options=[
                ft.dropdown.Option("1", "1 - Pruebas"),
                ft.dropdown.Option("2", "2 - Producción"),
            ],
            expand=True,
        )
        tf_estab = ft.TextField(label="Establecimiento", value=str(self.company_info.get("establecimiento", "001")), expand=True)
        tf_pto = ft.TextField(label="Punto de Emisión", value=str(self.company_info.get("punto_emision", "001")), expand=True)
        dd_obliga = ft.Dropdown(
            label="Obligado a llevar Contabilidad",
            value=self.company_info.get("obligado_contabilidad", "SI"),
            options=[
                ft.dropdown.Option("SI", "SÍ"),
                ft.dropdown.Option("NO", "NO"),
            ],
            expand=True,
        )
        tf_contrib = ft.TextField(label="N° Contribuyente Especial (Opcional)", value=self.company_info.get("contribuyente_especial", ""), expand=True)
        tf_sri_email = ft.TextField(label="Email SRI para Facturación", value=self.company_info.get("sri_email", "recepcion.sri@sri.gob.ec"), expand=True)

        # Numeración inicial de comprobantes
        tf_sec_factura = ft.TextField(
            label="Número para iniciar facturación",
            value=str(self.company_info.get("secuencial_factura", 1)),
            hint_text="Ej: 1",
            keyboard_type=ft.KeyboardType.NUMBER,
            expand=True,
        )
        tf_sec_cotizacion = ft.TextField(
            label="Número para iniciar cotizaciones",
            value=str(self.company_info.get("secuencial_cotizacion", 1)),
            hint_text="Ej: 1",
            keyboard_type=ft.KeyboardType.NUMBER,
            expand=True,
        )

        # Signature File Config - allow typing/pasting or file picking
        tf_firma_path = ft.TextField(
            label="Ruta Certificado Digital (.p12 / .pfx)",
            value=self.company_info.get("firma_path", ""),
            hint_text="Ej: /home/usuario/firma.p12 o usa Examinar",
            read_only=False,
            expand=True
        )
        tf_firma_pass = ft.TextField(
            label="Contraseña de la Firma Electrónica",
            value=self.company_info.get("firma_pass", ""),
            password=True,
            can_reveal_password=True,
            expand=True
        )

        # Selector de archivos. En Flet 1.x FilePicker es un servicio y
        # pick_files() es una corrutina: debe ejecutarse con run_task/await.
        file_picker = get_file_picker(self.page)
        can_update = AppState.has_permission("can_update", "company")

        # Logo de la empresa para facturas y cotizaciones
        logo_preview = ft.Container(
            width=230,
            height=120,
            padding=10,
            bgcolor=T.SURFACE_ALT,
            border_radius=8,
            border=_all_border(1, T.SURFACE_ALT),
            alignment=ft.Alignment(0, 0),
        )
        logo_status = ft.Text(size=12, color=T.TEXT_MUTED)

        def refresh_logo_preview():
            logo_path = str(self.company_info.get("logo_path") or "").strip()
            if logo_path and os.path.isfile(logo_path):
                logo_preview.content = ft.Image(
                    src=logo_path,
                    width=210,
                    height=100,
                    fit=ft.BoxFit.CONTAIN,
                )
                logo_status.value = f"Logo personalizado: {os.path.basename(logo_path)}"
                logo_status.color = T.SUCCESS_TEXT
            else:
                logo_preview.content = ft.Column(
                    controls=[
                        ft.Icon(
                            ft.Icons.IMAGE_NOT_SUPPORTED_ROUNDED,
                            size=34,
                            color=T.TEXT_SUBTLE,
                        ),
                        ft.Text(
                            "Sin logo personalizado",
                            size=11,
                            color=T.TEXT_MUTED,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4,
                )
                logo_status.value = (
                    "Se usará el logo predeterminado de la app."
                    if not logo_path
                    else "El archivo de logo no existe; se usará el predeterminado."
                )
                logo_status.color = T.TEXT_MUTED
            self.page.update()

        def trigger_logo_pick(e):
            if not can_update:
                show_toast("No tienes permisos de modificación.", is_error=True)
                return

            async def pick_logo():
                try:
                    files = await file_picker.pick_files(
                        dialog_title="Seleccionar logo de la empresa",
                        file_type=ft.FilePickerFileType.CUSTOM,
                        allowed_extensions=["jpg", "jpeg", "png", "webp"],
                        allow_multiple=False,
                        with_data=True,
                    )
                except Exception as exc:  # noqa: BLE001
                    show_toast(
                        f"No se pudo abrir el selector de archivos: {exc}",
                        is_error=True,
                    )
                    return

                if not files:
                    return

                chosen = files[0]
                path_val = chosen.path
                temp_path = None

                # En web/Android el selector puede devolver solo los bytes.
                if not path_val and chosen.bytes:
                    suffix = os.path.splitext(chosen.name or "")[1].lower() or ".png"
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                    tmp.write(chosen.bytes)
                    tmp.close()
                    path_val = tmp.name
                    temp_path = path_val

                if not path_val:
                    show_toast(
                        "No se pudo leer el logo seleccionado. Intenta de nuevo.",
                        is_error=True,
                    )
                    return

                try:
                    success, msg = CompanyController.upload_logo(path_val)
                finally:
                    if temp_path:
                        try:
                            os.unlink(temp_path)
                        except OSError:
                            pass

                if success:
                    self.company_info = CompanyController.get_info()
                    refresh_logo_preview()
                    show_toast(msg)
                else:
                    show_toast(msg, is_error=True)

            self.page.run_task(pick_logo)

        def remove_company_logo(e):
            if not can_update:
                show_toast("No tienes permisos de modificación.", is_error=True)
                return

            success, msg = CompanyController.remove_logo()
            if success:
                self.company_info = CompanyController.get_info()
                refresh_logo_preview()
                show_toast(msg)
            else:
                show_toast(msg, is_error=True)

        refresh_logo_preview()

        def trigger_file_pick(e):
            async def pick():
                try:
                    files = await file_picker.pick_files(
                        dialog_title="Seleccionar Firma Electrónica (.p12 / .pfx)",
                        file_type=ft.FilePickerFileType.CUSTOM,
                        allowed_extensions=["p12", "pfx"],
                        allow_multiple=False,
                        with_data=True,
                    )
                except Exception as exc:  # noqa: BLE001
                    show_toast(
                        f"No se pudo abrir el selector de archivos: {exc}",
                        is_error=True,
                    )
                    return

                if not files:
                    return

                chosen = files[0]
                path_val = chosen.path

                # En web/Android el selector puede devolver solo los bytes
                # (sin ruta accesible). Los guardamos en un temporal para que
                # SignatureService pueda copiarlos al almacenamiento de la app.
                if not path_val and chosen.bytes:
                    suffix = os.path.splitext(chosen.name or "")[1].lower() or ".p12"
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                    tmp.write(chosen.bytes)
                    tmp.close()
                    path_val = tmp.name

                if not path_val:
                    show_toast(
                        "No se pudo leer el archivo seleccionado. Intenta de nuevo.",
                        is_error=True,
                    )
                    return

                tf_firma_path.value = path_val
                self.page.update()
                show_toast(f"Firma seleccionada: {chosen.name or os.path.basename(path_val)}")

            self.page.run_task(pick)

        def save_signature_file(e):
            path_val = (tf_firma_path.value or "").strip()
            if not path_val:
                show_toast("Ingrese o seleccione un archivo de firma .p12 o .pfx", is_error=True)
                return
            
            success, msg = CompanyController.upload_signature(path_val, tf_firma_pass.value)
            if success:
                show_toast(msg)
                self.company_info = CompanyController.get_info()
                tf_firma_path.value = self.company_info.get("firma_path", "")
                render_badge()
            else:
                show_toast(msg, is_error=True)

        # SMTP Email Config
        tf_smtp_host = ft.TextField(label="Servidor SMTP", value=self.company_info.get("smtp_host", "smtp.gmail.com"), expand=True)
        tf_smtp_port = ft.TextField(label="Puerto SMTP", value=str(self.company_info.get("smtp_port", 587)), expand=True)
        tf_smtp_user = ft.TextField(label="Usuario SMTP (Email Salida)", value=self.company_info.get("smtp_user", ""), expand=True)
        tf_smtp_pass = ft.TextField(label="Contraseña SMTP / App Password", value=self.company_info.get("smtp_pass", ""), password=True, can_reveal_password=True, expand=True)
        sw_smtp_ssl = ft.Switch(label="Usar SSL directo (Puerto 465)", value=bool(self.company_info.get("smtp_ssl", 0)))

        def save_company_data(e):
            can_update = AppState.has_permission("can_update", "company")
            if not can_update:
                show_toast("No tienes permisos de modificación.", is_error=True)
                return

            success, res = CompanyController.update_info(
                ruc=tf_ruc.value,
                razon_social=tf_razon.value,
                nombre_comercial=tf_comercial.value,
                direccion_matriz=tf_matriz.value,
                direccion_establecimiento=tf_dir_estab.value,
                agente_retencion=tf_agente.value,
                telefono=tf_tel.value,
                email=tf_email.value,
                ambiente_sri=dd_ambiente.value,
                establecimiento=tf_estab.value,
                punto_emision=tf_pto.value,
                contribuyente_especial=tf_contrib.value,
                obligado_contabilidad=dd_obliga.value,
                sri_email=tf_sri_email.value,
                smtp_host=tf_smtp_host.value,
                smtp_port=tf_smtp_port.value,
                smtp_user=tf_smtp_user.value,
                smtp_pass=tf_smtp_pass.value,
                smtp_ssl=sw_smtp_ssl.value,
                secuencial_factura=tf_sec_factura.value,
                secuencial_cotizacion=tf_sec_cotizacion.value,
            )

            if success:
                show_toast("Datos de la empresa y configuración guardados con éxito.")
                self.company_info = CompanyController.get_info()
                tf_sec_factura.value = str(self.company_info.get("secuencial_factura", 1))
                tf_sec_cotizacion.value = str(self.company_info.get("secuencial_cotizacion", 1))
                render_badge()
            else:
                show_toast(res, is_error=True)

        # Signature Status Badge Container
        signature_badge_container = ft.Container()

        def render_badge():
            has_firma = bool(self.company_info.get("firma_path")) and os.path.exists(self.company_info.get("firma_path", ""))
            signature_badge_container.content = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.VERIFIED_USER_ROUNDED if has_firma else ft.Icons.WARNING_AMBER_ROUNDED, color=T.SUCCESS_TEXT if has_firma else T.WARNING, size=20),
                    ft.Text("Firma Electrónica Cargada y Vigente" if has_firma else "Firma Electrónica Pendiente", color=T.SUCCESS_TEXT if has_firma else T.WARNING, weight=ft.FontWeight.BOLD, size=12),
                ],
                spacing=8,
            )
            signature_badge_container.bgcolor = T.SUCCESS_BG if has_firma else T.WARNING_BG
            signature_badge_container.padding = ft.Padding.symmetric(horizontal=12, vertical=6)
            signature_badge_container.border_radius = 8
            self.page.update()

        render_badge()

        header_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.BUSINESS_ROUNDED, size=28, color=T.PINK),
                            ft.Column(
                                controls=[
                                    ft.Text("Datos del Negocio y Firma Electrónica", size=20, weight=ft.FontWeight.BOLD, color=T.TEXT),
                                    ft.Text("Configuración legal, parámetros SRI, logo, certificado digital .p12 y correo", size=12, color=T.TEXT_MUTED),
                                ],
                                spacing=0,
                            ),
                        ],
                        spacing=12,
                    ),
                    signature_badge_container,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=16,
            bgcolor=T.SURFACE,
            border_radius=10,
            border=_all_border(1, T.SURFACE_ALT),
        )

        # Section 1: Business Details
        sec_business = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Información General del Establecimiento", size=15, weight=ft.FontWeight.BOLD, color=T.INFO_TEXT),
                    ft.Row([tf_ruc, tf_razon, tf_comercial], spacing=10),
                    ft.Row([tf_tel, tf_email], spacing=10),
                    tf_matriz,
                    tf_dir_estab,
                    tf_agente,
                ],
                spacing=12,
            ),
            padding=16,
            bgcolor=T.SURFACE,
            border_radius=10,
            border=_all_border(1, T.SURFACE_ALT),
        )

        # Section 2: Company Logo
        sec_logo = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Logo de la Empresa (Facturas y Cotizaciones)",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=T.PINK,
                    ),
                    ft.Text(
                        "El logo se mostrará en el encabezado de las facturas y cotizaciones generadas en PDF.",
                        size=12,
                        color=T.TEXT_MUTED,
                    ),
                    ft.Row(
                        controls=[
                            logo_preview,
                            ft.Column(
                                controls=[
                                    logo_status,
                                    ft.Row(
                                        controls=[
                                            ft.FilledButton(
                                                "Seleccionar logo",
                                                icon=ft.Icons.IMAGE_ROUNDED,
                                                style=ft.ButtonStyle(
                                                    bgcolor=T.PRIMARY,
                                                    color=T.ON_ACCENT,
                                                ),
                                                on_click=trigger_logo_pick,
                                                disabled=not can_update,
                                            ),
                                            ft.OutlinedButton(
                                                "Quitar logo",
                                                icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                                                on_click=remove_company_logo,
                                                disabled=not can_update,
                                            ),
                                        ],
                                        spacing=10,
                                        wrap=True,
                                    ),
                                ],
                                spacing=8,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=18,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        wrap=True,
                    ),
                ],
                spacing=12,
            ),
            padding=16,
            bgcolor=T.SURFACE,
            border_radius=10,
            border=_all_border(1, T.SURFACE_ALT),
        )

        # Section 3: Numeración inicial de comprobantes
        sec_numeracion = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Numeración de Facturas y Cotizaciones",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=T.CYAN_TEXT,
                    ),
                    ft.Text(
                        "Indica el número con el que deseas comenzar. Se usará en el próximo comprobante y luego se incrementará automáticamente.",
                        size=12,
                        color=T.TEXT_MUTED,
                    ),
                    ft.Text(
                        "Si ya existen facturas o cotizaciones emitidas, usa un número mayor al último para evitar duplicados.",
                        size=11,
                        color=T.WARNING,
                    ),
                    ft.Row(
                        [tf_sec_factura, tf_sec_cotizacion],
                        spacing=10,
                    ),
                    ft.Text(
                        "Ejemplo: si escribes 100, la próxima factura será 001-001-000000100.",
                        size=11,
                        color=T.TEXT_SUBTLE,
                    ),
                ],
                spacing=12,
            ),
            padding=16,
            bgcolor=T.SURFACE,
            border_radius=10,
            border=_all_border(1, T.SURFACE_ALT),
        )

        # Section 4: SRI Parameters
        sec_sri = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Parámetros Tributarios (SRI Ecuador)", size=15, weight=ft.FontWeight.BOLD, color=T.PURPLE),
                    ft.Row([dd_ambiente, tf_estab, tf_pto], spacing=10),
                    ft.Row([dd_obliga, tf_contrib, tf_sri_email], spacing=10),
                ],
                spacing=12,
            ),
            padding=16,
            bgcolor=T.SURFACE,
            border_radius=10,
            border=_all_border(1, T.SURFACE_ALT),
        )

        # Section 3: Digital Signature Upload
        sec_signature = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Firma Electrónica Digital (.p12 / .pfx)", size=15, weight=ft.FontWeight.BOLD, color=T.SUCCESS_TEXT),
                    ft.Row(
                        controls=[
                            tf_firma_path,
                            ft.FilledButton(
                                "Examinar...",
                                icon=ft.Icons.FOLDER_OPEN_ROUNDED,
                                style=ft.ButtonStyle(bgcolor=T.DISABLED_BG, color=T.ON_ACCENT),
                                on_click=trigger_file_pick,
                                height=48,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Row(
                        controls=[
                            tf_firma_pass,
                            ft.FilledButton(
                                "Guardar Firma",
                                icon=ft.Icons.KEY_ROUNDED,
                                style=ft.ButtonStyle(bgcolor=T.SUCCESS_STRONG, color=T.ON_ACCENT),
                                on_click=save_signature_file,
                                height=48,
                            ),
                        ],
                        spacing=10,
                    ),
                ],
                spacing=12,
            ),
            padding=16,
            bgcolor=T.SURFACE,
            border_radius=10,
            border=_all_border(1, T.SURFACE_ALT),
        )

        # Section 4: Email SMTP Configuration
        sec_smtp = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Configuración de Servidor de Correo (Envío de Facturas)", size=15, weight=ft.FontWeight.BOLD, color=T.WARNING),
                    ft.Row([tf_smtp_host, tf_smtp_port], spacing=10),
                    ft.Row([tf_smtp_user, tf_smtp_pass], spacing=10),
                    sw_smtp_ssl,
                ],
                spacing=12,
            ),
            padding=16,
            bgcolor=T.SURFACE,
            border_radius=10,
            border=_all_border(1, T.SURFACE_ALT),
        )

        btn_save_all = ft.FilledButton(
            "Guardar Toda la Configuración",
            icon=ft.Icons.SAVE_ROUNDED,
            style=ft.ButtonStyle(bgcolor=T.PRIMARY, color=T.ON_ACCENT),
            on_click=save_company_data,
            height=46,
        )

        main_content = ft.Column(
            controls=[
                header_card,
                ft.Container(height=10),
                sec_business,
                ft.Container(height=10),
                sec_logo,
                ft.Container(height=10),
                sec_numeracion,
                ft.Container(height=10),
                sec_sri,
                ft.Container(height=10),
                sec_signature,
                ft.Container(height=10),
                sec_smtp,
                ft.Container(height=10),
                ft.Row([btn_save_all], alignment=ft.MainAxisAlignment.END),
                ft.Container(height=20),
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )

        return MainLayout(page=self.page, content=main_content, router=self.router)
