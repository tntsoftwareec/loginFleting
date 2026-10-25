import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import qrcode

from tests.base import ensure_faker

ensure_faker()

from app.services.pdf_service import PDFService, _tipo_identificacion_label


COMPANY = {
    "razon_social": "EMPRESA DEMO S.A.",
    "nombre_comercial": "DEMO",
    "direccion_matriz": "Av. Amazonas 123, Quito",
    "direccion_establecimiento": "Av. Amazonas 123, Quito",
    "ruc": "1790000000001",
    "contribuyente_especial": "",
    "obligado_contabilidad": "NO",
    "telefono": "0999999999",
    "email": "demo@demo.com",
    "ambiente_sri": 1,
}

INVOICE = {
    "secuencial": "001-001-000000001",
    "fecha_emision": "2026-10-24",
    "client_nombre": "JUAN PEREZ",
    "client_identificacion": "1710034065",
    "client_direccion": "Quito",
    "client_email": "juan@mail.com",
    "forma_pago": "EFECTIVO",
    "client_tipo_doc": "CEDULA",
    "subtotal_sin_impuestos": 100.0,
    "subtotal_0": 0.0,
    "subtotal_15": 100.0,
    "total_descuento": 0.0,
    "iva_total": 15.0,
    "importe_total": 115.0,
}

ITEMS = [
    {
        "codigo": "P001",
        "descripcion": "Producto de prueba",
        "cantidad": 1,
        "precio_unitario": 100.0,
        "descuento": 0.0,
        "subtotal": 100.0,
    }
]

CLAVE_ACCESO = "2410202601179000000000110010010000000011234567811"


def _pdf_text(path: str) -> str:
    if not shutil.which("pdftotext"):
        return ""
    result = subprocess.run(
        ["pdftotext", path, "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout


class PDFServiceTest(unittest.TestCase):
    def test_tipo_identificacion_label(self):
        self.assertEqual(
            _tipo_identificacion_label("CEDULA", "1710034065"), "Cédula"
        )
        self.assertEqual(
            _tipo_identificacion_label("RUC", "1790000000001"), "RUC"
        )
        self.assertEqual(
            _tipo_identificacion_label("CONSUMIDOR_FINAL", "9999999999999"),
            "Consumidor Final",
        )
        self.assertEqual(
            _tipo_identificacion_label("PASAPORTE", "AB1234567"), "Pasaporte"
        )

    def test_ride_includes_access_key_in_barcode_and_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("app.services.pdf_service.GENERATED_DIR", Path(tmp)):
                path = PDFService.generate_factura_pdf(
                    COMPANY, INVOICE, ITEMS, CLAVE_ACCESO
                )

                self.assertTrue(Path(path).is_file())
                self.assertGreater(Path(path).stat().st_size, 1000)

                text = _pdf_text(path)
                if not text:
                    self.skipTest("pdftotext no está disponible")
                self.assertIn(CLAVE_ACCESO, text)
                self.assertIn("PENDIENTE DE AUTORIZACION", text)

    def test_ride_shows_authorization_number_and_date(self):
        fecha = "2026-10-24T20:15:00-05:00"
        with tempfile.TemporaryDirectory() as tmp:
            with patch("app.services.pdf_service.GENERATED_DIR", Path(tmp)):
                path = PDFService.generate_factura_pdf(
                    COMPANY,
                    INVOICE,
                    ITEMS,
                    CLAVE_ACCESO,
                    autorizacion={
                        "estado": "AUTORIZADO",
                        "numero": CLAVE_ACCESO,
                        "fecha": fecha,
                    },
                )

                text = _pdf_text(path)
                if not text:
                    self.skipTest("pdftotext no está disponible")
                self.assertIn("Numero de Autorizacion", text)
                self.assertIn(fecha, text)
                self.assertNotIn("PENDIENTE DE AUTORIZACION", text)

    def test_ride_includes_ice_propina_agente_y_forma_pago(self):
        company = dict(COMPANY, agente_retencion="1234567890")
        invoice = dict(
            INVOICE,
            ice_total=10.0,
            propina=2.0,
            importe_total=178.5,
            forma_pago="TARJETA_CREDITO",
        )
        items = [
            dict(
                ITEMS[0],
                subtotal=100.0,
                valor_ice=10.0,
                ice_codigo="3031",
                ice_porcentaje=10.0,
                valor_iva=16.5,
                total=126.5,
            )
        ]
        with tempfile.TemporaryDirectory() as tmp:
            with patch("app.services.pdf_service.GENERATED_DIR", Path(tmp)):
                path = PDFService.generate_factura_pdf(
                    company, invoice, items, CLAVE_ACCESO
                )

                self.assertTrue(Path(path).is_file())
                text = _pdf_text(path)
                if not text:
                    self.skipTest("pdftotext no está disponible")
                self.assertIn("Agente de Retencion", text)
                self.assertIn("Tarjeta de crédito", text)
                self.assertIn("ICE", text)
                self.assertIn("Propina", text)

    def test_qr_contains_sri_verification_url(self):
        captured = {}
        original_add_data = qrcode.QRCode.add_data

        def fake_add_data(qr_self, data, *args, **kwargs):
            captured["data"] = data
            return original_add_data(qr_self, data, *args, **kwargs)

        with tempfile.TemporaryDirectory() as tmp:
            with patch("app.services.pdf_service.GENERATED_DIR", Path(tmp)):
                with patch.object(qrcode.QRCode, "add_data", fake_add_data):
                    PDFService.generate_factura_pdf(
                        COMPANY, INVOICE, ITEMS, CLAVE_ACCESO
                    )

        data = captured.get("data", "")
        self.assertTrue(data.startswith("https://srienlinea.sri.gob.ec/"))
        self.assertIn(CLAVE_ACCESO, data)


if __name__ == "__main__":
    unittest.main()
