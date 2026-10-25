import unittest
from unittest.mock import patch

from tests.base import ensure_faker

ensure_faker()

from app.controllers.company_controller import CompanyController
from app.controllers.invoice_controller import InvoiceController
from app.models.invoice_model import InvoiceModel
from app.services.email_service import EmailService
from app.services.sri_service import SRIService


CLAVE_ACCESO = "2410202601179000000000110010010000000011234567811"

COMPANY = {
    "razon_social": "EMPRESA DEMO S.A.",
    "nombre_comercial": "DEMO",
    "ruc": "1790000000001",
    "ambiente_sri": 1,
    "establecimiento": "001",
    "punto_emision": "001",
    "direccion_matriz": "Av. Matriz 123",
    "direccion_establecimiento": "Av. Estab 456",
    "agente_retencion": "",
    "contribuyente_especial": "",
    "obligado_contabilidad": "NO",
    "email": "demo@demo.com",
    "smtp_host": "smtp.demo.com",
    "smtp_port": 587,
    "smtp_user": "demo@demo.com",
    "smtp_pass": "",
    "smtp_ssl": 0,
}

INVOICE = {
    "id": 1,
    "secuencial": "001-001-000000001",
    "clave_acceso": CLAVE_ACCESO,
    "client_tipo_doc": "CEDULA",
    "client_nombre": "JUAN PEREZ",
    "client_identificacion": "1710034065",
    "client_email": "juan@mail.com",
    "client_direccion": "Quito",
    "fecha_emision": "2026-10-24",
    "subtotal_15": 100.0,
    "subtotal_0": 0.0,
    "subtotal_sin_impuestos": 100.0,
    "total_descuento": 0.0,
    "iva_total": 16.5,
    "ice_total": 10.0,
    "propina": 2.0,
    "importe_total": 128.5,
    "forma_pago": "TARJETA_CREDITO",
    "email_estado": "PENDIENTE",
    "pdf_path": "/tmp/ride_pendiente.pdf",
    "xml_path": "/tmp/firmado.xml",
    "sri_autorizacion": "",
    "sri_fecha_autorizacion": "",
    "items": [],
}

SRI_RESULT = {
    "estado": "AUTORIZADO",
    "mensaje": "AUTORIZADO",
    "respuesta": "AUTORIZADO",
    "recepcion": {"estado": "RECIBIDA"},
    "autorizacion": {"estado": "AUTORIZADO"},
    "clave_acceso": CLAVE_ACCESO,
    "numero_autorizacion": "1234567890",
    "fecha_autorizacion": "2026-10-24T20:00:00-05:00",
    "xml_firmado_path": "/tmp/firmado.xml",
    "xml_autorizado_path": "/tmp/autorizado.xml",
}


class InvoiceEmailFlowTest(unittest.TestCase):
    def test_email_is_sent_only_after_authorization(self):
        with patch.object(InvoiceController, "get_by_id", return_value=INVOICE), \
             patch.object(CompanyController, "get_info", return_value=COMPANY), \
             patch.object(
                 InvoiceController,
                 "_ensure_invoice_xml",
                 return_value=(True, "/tmp/firmado.xml"),
             ), \
             patch.object(
                 SRIService, "send_invoice", return_value=(True, SRI_RESULT)
             ), \
             patch.object(
                 InvoiceController,
                 "_regenerate_invoice_pdf",
                 return_value="/tmp/ride_autorizado.pdf",
             ), \
             patch.object(
                 EmailService,
                 "send_invoice_email",
                 return_value=(True, "Factura enviada"),
             ) as email_mock, \
             patch.object(InvoiceModel, "update_by_id") as update_mock:
            ok, result = InvoiceController.send_to_sri(1)

        self.assertTrue(ok)
        self.assertTrue(email_mock.called)
        args = email_mock.call_args[0]
        self.assertEqual(args[2], "/tmp/autorizado.xml")
        self.assertEqual(args[3], "/tmp/ride_autorizado.pdf")
        self.assertEqual(result.get("email_status"), "Factura enviada")
        update_mock.assert_any_call(1, email_estado="ENVIADA")

    def test_email_is_not_sent_when_user_disabled_it(self):
        invoice = dict(INVOICE, email_estado="NO_ENVIAR")
        with patch.object(InvoiceController, "get_by_id", return_value=invoice), \
             patch.object(CompanyController, "get_info", return_value=COMPANY), \
             patch.object(
                 InvoiceController,
                 "_ensure_invoice_xml",
                 return_value=(True, "/tmp/firmado.xml"),
             ), \
             patch.object(
                 SRIService, "send_invoice", return_value=(True, SRI_RESULT)
             ), \
             patch.object(
                 InvoiceController,
                 "_regenerate_invoice_pdf",
                 return_value="/tmp/ride_autorizado.pdf",
             ), \
             patch.object(EmailService, "send_invoice_email") as email_mock, \
             patch.object(InvoiceModel, "update_by_id"):
            ok, result = InvoiceController.send_to_sri(1)

        self.assertTrue(ok)
        self.assertFalse(email_mock.called)
        self.assertEqual(result.get("email_status"), "Envío por correo desactivado.")

    def test_authorized_invoice_is_not_resent_to_sri(self):
        invoice = dict(
            INVOICE,
            estado="AUTORIZADO",
            sri_autorizacion="1234567890",
            sri_fecha_autorizacion="2026-10-24T20:00:00-05:00",
            sri_respuesta="ESTADO SRI: AUTORIZADO",
        )
        with patch.object(InvoiceController, "get_by_id", return_value=invoice), \
             patch.object(CompanyController, "get_info", return_value=COMPANY), \
             patch.object(
                 InvoiceController,
                 "_regenerate_invoice_pdf",
                 return_value="/tmp/ride_autorizado.pdf",
             ), \
             patch.object(SRIService, "send_invoice") as send_mock:
            ok, result = InvoiceController.send_to_sri(1)

        self.assertTrue(ok)
        self.assertFalse(send_mock.called)
        self.assertEqual(result["estado"], "AUTORIZADO")
        self.assertEqual(result["numero_autorizacion"], "1234567890")
        self.assertIn("ya está autorizada", result["email_status"])


if __name__ == "__main__":
    unittest.main()
