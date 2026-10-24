import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from core.logger import get_logger

logger = get_logger("EmailService")


def _text(value) -> str:
    """Convierte un valor de la BD en texto seguro (nunca None)."""
    return str(value).strip() if value is not None else ""


def _to_float(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _to_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _is_true(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return _text(value).lower() in ("1", "true", "si", "sí", "yes", "on")


def _is_valid_email(value: str) -> bool:
    value = _text(value)
    if not value or " " in value or value.count("@") != 1:
        return False
    local, domain = value.rsplit("@", 1)
    return bool(local) and "." in domain and not domain.startswith(".") and not domain.endswith(".")


def _file_exists(path: str) -> bool:
    try:
        return bool(path) and os.path.isfile(path)
    except (TypeError, ValueError):
        return False


def _attach_file(msg: MIMEMultipart, path: str, subtype: str) -> bool:
    if not _file_exists(path):
        return False
    with open(path, "rb") as handle:
        attachment = MIMEApplication(handle.read(), _subtype=subtype)
    attachment.add_header(
        "Content-Disposition",
        "attachment",
        filename=Path(path).name,
    )
    msg.attach(attachment)
    return True


class EmailService:
    """Envío de facturas y cotizaciones por SMTP."""

    @classmethod
    def _deliver(cls, company_info: dict, msg: MIMEMultipart, recipients: list[str]) -> tuple:
        """Entrega el mensaje por SMTP y devuelve ``(ok, error)``.

        La contraseña debe llegar en texto plano desde ``CompanyController``;
        nunca se guarda ni se registra en los logs.
        """
        smtp_host = _text(company_info.get("smtp_host")) or "smtp.gmail.com"
        smtp_port = _to_int(company_info.get("smtp_port"), 587)
        smtp_user = _text(company_info.get("smtp_user"))
        smtp_pass = _text(company_info.get("smtp_pass"))
        use_ssl = _is_true(company_info.get("smtp_ssl"))

        if not smtp_user or not smtp_pass:
            return False, (
                "El correo SMTP no está configurado. Ve a Mi Empresa, escribe "
                "el usuario y la contraseña de aplicación SMTP, y guarda los cambios."
            )

        server = None
        try:
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=20)
                server.ehlo()
                server.starttls()
                server.ehlo()

            server.login(smtp_user, smtp_pass)
            refused = server.sendmail(msg["From"], recipients, msg.as_string())
            if refused:
                logger.warning("Destinatarios rechazados por SMTP: %s", refused)
                return False, (
                    "El servidor SMTP rechazó algunos destinatarios: "
                    + ", ".join(refused.keys())
                )
            return True, ""
        except smtplib.SMTPAuthenticationError as exc:
            logger.error("Autenticación SMTP rechazada: %s", exc)
            return False, (
                "El servidor SMTP rechazó el usuario o la contraseña. "
                "Si usas Gmail, necesitas una contraseña de aplicación, no tu "
                "contraseña normal. Revisa la configuración en Mi Empresa."
            )
        except (smtplib.SMTPException, OSError) as exc:
            logger.error("Error al enviar correo SMTP: %s", exc)
            return False, f"No se pudo enviar el correo por SMTP: {exc}"
        except Exception as exc:  # noqa: BLE001
            logger.error("Error inesperado al enviar correo SMTP: %s", exc)
            return False, f"No se pudo enviar el correo: {exc}"
        finally:
            if server is not None:
                try:
                    server.quit()
                except (smtplib.SMTPException, OSError):
                    pass

    @classmethod
    def send_invoice_email(
        cls,
        company_info: dict,
        invoice_data: dict,
        xml_path: str,
        pdf_path: str,
    ) -> tuple:
        """Envía la factura en PDF y XML al cliente y al SRI.

        Returns:
            (success: bool, message: str)
        """
        client_email = _text(invoice_data.get("client_email"))
        sri_email = _text(company_info.get("sri_email")) or "recepcion.sri@sri.gob.ec"

        recipients = []
        if _is_valid_email(client_email) and client_email.lower() != "consumidor@mail.com":
            recipients.append(client_email)
        if _is_valid_email(sri_email):
            recipients.append(sri_email)

        # Evita duplicados conservando el orden.
        recipients = list(dict.fromkeys(recipients))

        if not recipients:
            return False, "No hay destinatarios de correo válidos para enviar la factura."
        if not _file_exists(pdf_path) and not _file_exists(xml_path):
            return False, "No se encontraron el PDF ni el XML de la factura."

        secuencial = invoice_data.get("secuencial", "")
        company_name = _text(company_info.get("razon_social")) or "Fletting Solutions"

        msg = MIMEMultipart()
        msg["From"] = _text(company_info.get("smtp_user")) or f"Facturación <no-reply@{company_host(company_info.get('smtp_host', ''))}>"
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = f"Comprobante Electrónico Factura N° {secuencial} - {company_name}"

        body = f"""
Estimado(a) {invoice_data.get('client_nombre', 'Cliente')},

Adjunto a este correo encontrará su Factura Electrónica N° {secuencial} emitida por {company_name}.

Detalles de la transacción:
- Fecha de Emisión: {invoice_data.get('fecha_emision')}
- Clave de Acceso: {invoice_data.get('clave_acceso')}
- Importe Total: ${_to_float(invoice_data.get('importe_total')):.2f}

Adjuntos:
1. Documento en formato PDF (RIDE)
2. Archivo en formato XML (Comprobante Electrónico)

Gracias por su preferencia.
--
{company_name}
"""
        msg.attach(MIMEText(body, "plain", "utf-8"))

        _attach_file(msg, xml_path, "xml")
        _attach_file(msg, pdf_path, "pdf")

        ok, error = cls._deliver(company_info, msg, recipients)
        if not ok:
            return False, error

        logger.info(
            "Factura %s enviada exitosamente vía SMTP a %s",
            secuencial,
            ", ".join(recipients),
        )
        return True, f"Factura enviada exitosamente a {', '.join(recipients)}"

    @classmethod
    def send_quotation_email(
        cls,
        company_info: dict,
        quotation_data: dict,
        pdf_path: str,
    ) -> tuple:
        """Envía la cotización en PDF por correo electrónico al cliente.

        Returns:
            (success: bool, message: str)
        """
        client_email = _text(quotation_data.get("client_email"))

        if not _is_valid_email(client_email) or client_email.lower() == "consumidor@mail.com":
            return False, (
                "El cliente no tiene un correo electrónico válido. "
                "Actualiza el correo del cliente y vuelve a intentar."
            )
        if not _file_exists(pdf_path):
            return False, (
                "No se encontró el PDF de la cotización. "
                "Vuelve a generarla o abre el PDF para regenerarlo."
            )

        recipients = [client_email]
        secuencial = quotation_data.get("secuencial", "")
        company_name = _text(company_info.get("razon_social")) or "Fletting Solutions"

        msg = MIMEMultipart()
        msg["From"] = _text(company_info.get("smtp_user")) or f"Cotizaciones <no-reply@{company_host(company_info.get('smtp_host', ''))}>"
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = f"Cotización N° {secuencial} - {company_name}"

        notas = _text(quotation_data.get("notas"))
        body = f"""
Estimado(a) {quotation_data.get('client_nombre', 'Cliente')},

Adjunto a este correo encontrará la Cotización N° {secuencial} emitida por {company_name}.

Detalles:
- Fecha de Emisión: {quotation_data.get('fecha_emision')}
- Válida hasta: {quotation_data.get('fecha_validez')}
- Importe Total: ${_to_float(quotation_data.get('importe_total')):.2f}

{(f'Notas: {notas}') if notas else ''}

Adjuntos:
1. Cotización en formato PDF

Quedamos atentos a sus comentarios.
--
{company_name}
"""
        msg.attach(MIMEText(body, "plain", "utf-8"))
        _attach_file(msg, pdf_path, "pdf")

        ok, error = cls._deliver(company_info, msg, recipients)
        if not ok:
            return False, error

        logger.info(
            "Cotización %s enviada exitosamente vía SMTP a %s",
            secuencial,
            ", ".join(recipients),
        )
        return True, f"Cotización enviada exitosamente a {', '.join(recipients)}"


def company_host(host: str) -> str:
    host = _text(host)
    if not host:
        return "empresa.com"
    return host.replace("smtp.", "") if "smtp." in host else "empresa.com"
