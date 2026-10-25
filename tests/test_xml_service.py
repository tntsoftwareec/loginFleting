import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from tests.base import ensure_faker

ensure_faker()

from app.services.xml_service import XMLService


CLAVE_ACCESO = "2410202601179000000000110010010000000011234567811"

COMPANY = {
    "razon_social": "EMPRESA DEMO S.A.",
    "nombre_comercial": "DEMO",
    "ruc": "1790000000001",
    "ambiente_sri": 1,
    "establecimiento": "001",
    "punto_emision": "001",
    "direccion_matriz": "Av. Matriz 123",
    "direccion_establecimiento": "Av. Establecimiento 456",
    "agente_retencion": "1234567890",
    "contribuyente_especial": "",
    "obligado_contabilidad": "NO",
}

INVOICE = {
    "secuencial": "001-001-000000001",
    "clave_acceso": CLAVE_ACCESO,
    "fecha_emision": "2026-10-24",
    "client_tipo_doc": "CEDULA",
    "client_nombre": "JUAN PEREZ",
    "client_identificacion": "1710034065",
    "client_direccion": "Quito",
    "subtotal_sin_impuestos": 150.0,
    "subtotal_15": 100.0,
    "subtotal_0": 50.0,
    "total_descuento": 0.0,
    "iva_total": 16.5,
    "ice_total": 10.0,
    "propina": 2.0,
    "importe_total": 178.5,
    "forma_pago": "TARJETA_CREDITO",
}

ITEMS = [
    {
        "codigo": "P001",
        "descripcion": "Producto con ICE",
        "cantidad": 1,
        "precio_unitario": 100.0,
        "descuento": 0.0,
        "subtotal": 100.0,
        "iva_porcentaje": 15.0,
        "valor_iva": 16.5,
        "ice_codigo": "3031",
        "ice_porcentaje": 10.0,
        "valor_ice": 10.0,
        "total": 126.5,
    },
    {
        "codigo": "S001",
        "descripcion": "Servicio sin IVA",
        "cantidad": 1,
        "precio_unitario": 50.0,
        "descuento": 0.0,
        "subtotal": 50.0,
        "iva_porcentaje": 0.0,
        "valor_iva": 0.0,
        "ice_codigo": "",
        "ice_porcentaje": 0.0,
        "valor_ice": 0.0,
        "total": 50.0,
    },
]


class XMLServiceTest(unittest.TestCase):
    def _generate(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("app.services.xml_service.GENERATED_DIR", Path(tmp)):
                path, content, clave = XMLService.create_factura_xml(
                    COMPANY, INVOICE, ITEMS
                )
                self.assertTrue(Path(path).is_file())
                return ET.fromstring(content), clave

    def test_incluye_direccion_establecimiento_y_agente_retencion(self):
        root, _ = self._generate()
        self.assertEqual(
            root.findtext("./infoFactura/dirEstablecimiento"),
            "Av. Establecimiento 456",
        )
        self.assertEqual(
            root.findtext("./infoTributaria/agenteRetencion"),
            "1234567890",
        )

    def test_incluye_ice_propina_y_forma_pago(self):
        root, clave = self._generate()
        self.assertEqual(clave, CLAVE_ACCESO)
        self.assertEqual(root.findtext("./infoFactura/propina"), "2.00")
        self.assertEqual(root.findtext("./infoFactura/importeTotal"), "178.50")
        self.assertEqual(
            root.findtext("./infoFactura/pagos/pago/formaPago"), "19"
        )

        totales = root.findall("./infoFactura/totalConImpuestos/totalImpuesto")
        ice = [
            t for t in totales
            if t.findtext("codigo") == "3"
        ]
        self.assertEqual(len(ice), 1)
        self.assertEqual(ice[0].findtext("codigoPorcentaje"), "3031")
        self.assertEqual(ice[0].findtext("baseImponible"), "100.00")
        self.assertEqual(ice[0].findtext("valor"), "10.00")

        iva = [
            t for t in totales
            if t.findtext("codigo") == "2" and t.findtext("codigoPorcentaje") == "4"
        ]
        self.assertEqual(len(iva), 1)
        # La base del IVA incluye el ICE del ítem.
        self.assertEqual(iva[0].findtext("baseImponible"), "110.00")
        self.assertEqual(iva[0].findtext("valor"), "16.50")

    def test_detalle_incluye_impuesto_ice_y_base_iva_con_ice(self):
        root, _ = self._generate()
        detalles = root.findall("./detalles/detalle")
        self.assertEqual(len(detalles), 2)

        impuestos = detalles[0].findall("./impuestos/impuesto")
        codigos = {imp.findtext("codigo"): imp for imp in impuestos}
        self.assertIn("3", codigos)
        self.assertIn("2", codigos)
        self.assertEqual(codigos["3"].findtext("codigoPorcentaje"), "3031")
        self.assertEqual(codigos["3"].findtext("valor"), "10.00")
        self.assertEqual(codigos["2"].findtext("baseImponible"), "110.00")
        self.assertEqual(codigos["2"].findtext("valor"), "16.50")


if __name__ == "__main__":
    unittest.main()
