import os
import flet as ft
from app.views.layouts.main_layout import MainLayout
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
        if not AppState.has_permission("can_read"):
            content_layout = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.LOCK_OUTLINED, color="#ef4444", size=64),
                        ft.Text("Acceso Restringido", color="#f8fafc", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("No tienes permisos suficientes para acceder a este módulo.", color="#94a3b8", size=14),
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
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message, color="#ffffff"),
                bgcolor="#ef4444" if is_error else "#10b981",
                duration=3500
            )
            self.page.snack_bar.open = True
            self.page.update()

        self.company_info = CompanyController.get_info()

        # Form Fields - General Info
        tf_ruc = ft.TextField(label="R.U.C. Empresa", value=self.company_info.get("ruc", "1792998877001"), expand=True)
        tf_razon = ft.TextField(label="Razón Social", value=self.company_info.get("razon_social", "FLETING SOLUTIONS S.A.S."), expand=True)
        tf_comercial = ft.TextField(label="Nombre Comercial", value=self.company_info.get("nombre_comercial", "FLETING POS"), expand=True)
        tf_matriz = ft.TextField(label="Dirección Matriz", value=self.company_info.get("direccion_matriz", "Av. de los Granados N40-100"), multiline=True, max_lines=2, expand=True)
        tf_tel = ft.TextField(label="Teléfono Contacto", value=self.company_info.get("telefono", "0991234567"), expand=True)
        tf_email = ft.TextField(label="Email de la Empresa", value=self.company_info.get("email", "facturacion@fleting.ec"), expand=True)

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

        # FilePicker callback
        def on_file_picked(e):
            if e.files and len(e.files) > 0:
                picked_file_path = e.files[0].path
                tf_firma_path.value = picked_file_path
                self.page.update()
                show_toast(f"Firma seleccionada: {picked_file_path}")

        file_picker = ft.FilePicker()
        file_picker.on_result = on_file_picked

        def trigger_file_pick(e):
            try:
                if file_picker not in self.page.overlay:
                    self.page.overlay.append(file_picker)
                    self.page.update()
                file_picker.pick_files(
                    dialog_title="Seleccionar Firma Electrónica (.p12 / .pfx)",
                    allowed_extensions=["p12", "pfx"],
                    file_type=ft.FilePickerFileType.CUSTOM,
                )
            except Exception as ex:
                show_toast("Ingrese la ruta del archivo manualmente en el campo de texto.", is_error=True)

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
            can_update = AppState.has_permission("can_update")
            if not can_update:
                show_toast("No tienes permisos de modificación.", is_error=True)
                return

            success, res = CompanyController.update_info(
                ruc=tf_ruc.value,
                razon_social=tf_razon.value,
                nombre_comercial=tf_comercial.value,
                direccion_matriz=tf_matriz.value,
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
                smtp_ssl=sw_smtp_ssl.value
            )

            if success:
                show_toast("Datos de la empresa y configuración guardados con éxito.")
                self.company_info = CompanyController.get_info()
                render_badge()
            else:
                show_toast(res, is_error=True)

        # Signature Status Badge Container
        signature_badge_container = ft.Container()

        def render_badge():
            has_firma = bool(self.company_info.get("firma_path")) and os.path.exists(self.company_info.get("firma_path", ""))
            signature_badge_container.content = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.VERIFIED_USER_ROUNDED if has_firma else ft.Icons.WARNING_AMBER_ROUNDED, color="#34d399" if has_firma else "#fbbf24", size=20),
                    ft.Text("Firma Electrónica Cargada y Vigente" if has_firma else "Firma Electrónica Pendiente", color="#34d399" if has_firma else "#fbbf24", weight=ft.FontWeight.BOLD, size=12),
                ],
                spacing=8,
            )
            signature_badge_container.bgcolor = "#065f4633" if has_firma else "#78350f33"
            signature_badge_container.padding = ft.Padding.symmetric(horizontal=12, vertical=6)
            signature_badge_container.border_radius = 8
            self.page.update()

        render_badge()

        header_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.BUSINESS_ROUNDED, size=28, color="#ec4899"),
                            ft.Column(
                                controls=[
                                    ft.Text("Datos del Negocio y Firma Electrónica", size=20, weight=ft.FontWeight.BOLD, color="#f8fafc"),
                                    ft.Text("Configuración legal, parámetros SRI, certificado digital .p12 y correo", size=12, color="#94a3b8"),
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
            bgcolor="#0f172a",
            border_radius=10,
            border=_all_border(1, "#1e293b"),
        )

        # Section 1: Business Details
        sec_business = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Información General del Establecimiento", size=15, weight=ft.FontWeight.BOLD, color="#60a5fa"),
                    ft.Row([tf_ruc, tf_razon, tf_comercial], spacing=10),
                    ft.Row([tf_tel, tf_email], spacing=10),
                    tf_matriz,
                ],
                spacing=12,
            ),
            padding=16,
            bgcolor="#0f172a",
            border_radius=10,
            border=_all_border(1, "#1e293b"),
        )

        # Section 2: SRI Parameters
        sec_sri = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Parámetros Tributarios (SRI Ecuador)", size=15, weight=ft.FontWeight.BOLD, color="#a855f7"),
                    ft.Row([dd_ambiente, tf_estab, tf_pto], spacing=10),
                    ft.Row([dd_obliga, tf_contrib, tf_sri_email], spacing=10),
                ],
                spacing=12,
            ),
            padding=16,
            bgcolor="#0f172a",
            border_radius=10,
            border=_all_border(1, "#1e293b"),
        )

        # Section 3: Digital Signature Upload
        sec_signature = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Firma Electrónica Digital (.p12 / .pfx)", size=15, weight=ft.FontWeight.BOLD, color="#34d399"),
                    ft.Row(
                        controls=[
                            tf_firma_path,
                            ft.FilledButton(
                                "Examinar...",
                                icon=ft.Icons.FOLDER_OPEN_ROUNDED,
                                style=ft.ButtonStyle(bgcolor="#334155", color="#ffffff"),
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
                                style=ft.ButtonStyle(bgcolor="#059669", color="#ffffff"),
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
            bgcolor="#0f172a",
            border_radius=10,
            border=_all_border(1, "#1e293b"),
        )

        # Section 4: Email SMTP Configuration
        sec_smtp = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Configuración de Servidor de Correo (Envío de Facturas)", size=15, weight=ft.FontWeight.BOLD, color="#fbbf24"),
                    ft.Row([tf_smtp_host, tf_smtp_port], spacing=10),
                    ft.Row([tf_smtp_user, tf_smtp_pass], spacing=10),
                    sw_smtp_ssl,
                ],
                spacing=12,
            ),
            padding=16,
            bgcolor="#0f172a",
            border_radius=10,
            border=_all_border(1, "#1e293b"),
        )

        btn_save_all = ft.FilledButton(
            "Guardar Toda la Configuración",
            icon=ft.Icons.SAVE_ROUNDED,
            style=ft.ButtonStyle(bgcolor="#2563eb", color="#ffffff"),
            on_click=save_company_data,
            height=46,
        )

        main_content = ft.Column(
            controls=[
                header_card,
                ft.Container(height=10),
                sec_business,
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
