import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
from core.logger import get_logger

logger = get_logger("EmailService")

class EmailService:
    @classmethod
    def send_invoice_email(cls, company_info: dict, invoice_data: dict, xml_path: str, pdf_path: str) -> tuple:
        """Envía la factura en PDF y XML por correo electrónico al cliente y al SRI.
        
        Returns:
            (success: bool, message: str)
        """
        client_email = invoice_data.get("client_email", "").strip()
        sri_email = company_info.get("sri_email", "recepcion.sri@sri.gob.ec").strip()

        smtp_host = company_info.get("smtp_host", "smtp.gmail.com").strip()
        smtp_port = int(company_info.get("smtp_port", 587))
        smtp_user = company_info.get("smtp_user", "").strip()
        smtp_pass = company_info.get("smtp_pass", "").strip()

        recipients = []
        if client_email and "@" in client_email and client_email != "consumidor@mail.com":
            recipients.append(client_email)
        if sri_email and "@" in sri_email:
            recipients.append(sri_email)

        if not recipients:
            return False, "No hay destinatarios de correo válidos para enviar la factura."

        secuencial = invoice_data.get("secuencial", "")
        company_name = company_info.get("razon_social", "Fletting Solutions")

        # Create Email Message
        msg = MIMEMultipart()
        msg['From'] = smtp_user if smtp_user else f"Facturación <no-reply@{company_host(smtp_host)}>"
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = f"Comprobante Electrónico Factura N° {secuencial} - {company_name}"

        body = f"""
        Estimado(a) {invoice_data.get('client_nombre', 'Cliente')},

        Adjunto a este correo encontrará su Factura Electrónica N° {secuencial} emitida por {company_name}.

        Detalles de la transacción:
        - Fecha de Emisión: {invoice_data.get('fecha_emision')}
        - Clave de Acceso: {invoice_data.get('clave_acceso')}
        - Importe Total: ${invoice_data.get('importe_total', 0.0):.2f}

        Adjuntos:
        1. Documento en formato PDF (RIDE)
        2. Archivo en formato XML (Comprobante Electrónico)

        Gracias por su preferencia.
        --
        {company_name}
        """

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Attach XML
        if xml_path and os.path.exists(xml_path):
            with open(xml_path, 'rb') as f:
                attach_xml = MIMEApplication(f.read(), _subtype="xml")
                attach_xml.add_header('Content-Disposition', 'attachment', filename=Path(xml_path).name)
                msg.attach(attach_xml)

        # Attach PDF
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                attach_pdf = MIMEApplication(f.read(), _subtype="pdf")
                attach_pdf.add_header('Content-Disposition', 'attachment', filename=Path(pdf_path).name)
                msg.attach(attach_pdf)

        # Send via SMTP
        if not smtp_user or not smtp_pass:
            logger.info(f"[SIMULACIÓN DE ENVÍO SMTP] Factura {secuencial} enviada exitosamente a: {', '.join(recipients)}")
            return True, f"Simulación: Factura enviada correctamente a {', '.join(recipients)}"

        try:
            if company_info.get("smtp_ssl"):
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                server.starttls()

            server.login(smtp_user, smtp_pass)
            server.sendmail(msg['From'], recipients, msg.as_string())
            server.quit()
            logger.info(f"Factura {secuencial} enviada exitosamente vía SMTP a {', '.join(recipients)}")
            return True, f"Factura enviada exitosamente a {', '.join(recipients)}"
        except Exception as e:
            logger.error(f"Error al enviar correo SMTP: {e}")
            return False, f"No se pudo conectar al servidor SMTP: {str(e)}"

def company_host(host: str) -> str:
    return host.replace("smtp.", "") if "smtp." in host else "empresa.com"
