import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from tests.base import ensure_faker

ensure_faker()

from app.services import sri_service
from app.services.sri_service import (
    _find_first,
    _formatear_respuesta,
    _parse_mensajes,
    _tiene_error_clave_registrada,
    send_invoice,
)


CLAVE = "2410202601179000000000110010010000000011234567811"


class SRIServiceParsingTest(unittest.TestCase):
    def test_recepcion_devuelta_message_is_parsed(self):
        xml = """
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <soap:Body>
            <RespuestaRecepcionComprobante>
              <estado>DEVUELTA</estado>
              <comprobantes>
                <comprobante>
                  <claveAcceso>N/A</claveAcceso>
                  <mensajes>
                    <mensaje>
                      <identificador>35</identificador>
                      <mensaje>ARCHIVO NO CUMPLE ESTRUCTURA XML</mensaje>
                      <informacionAdicional>No existe el RUC</informacionAdicional>
                      <tipo>ERROR</tipo>
                    </mensaje>
                  </mensajes>
                </comprobante>
              </comprobantes>
            </RespuestaRecepcionComprobante>
          </soap:Body>
        </soap:Envelope>
        """
        root = ET.fromstring(xml)
        respuesta = _find_first(root, "RespuestaRecepcionComprobante")
        comprobante = _find_first(respuesta, "comprobante")
        mensajes = _parse_mensajes(comprobante)

        self.assertEqual(len(mensajes), 1)
        self.assertEqual(mensajes[0]["identificador"], "35")
        self.assertEqual(
            mensajes[0]["mensaje"], "ARCHIVO NO CUMPLE ESTRUCTURA XML"
        )
        self.assertEqual(mensajes[0]["tipo"], "ERROR")

    def test_formatted_response_includes_reception_and_authorization(self):
        recepcion = {
            "estado": "RECIBIDA",
            "mensajes": [],
        }
        autorizacion = {
            "estado": "AUTORIZADO",
            "numero": "1234567890",
            "fecha": "2026-10-23T12:00:00-05:00",
            "mensajes": [],
        }
        texto = _formatear_respuesta("AUTORIZADO", recepcion, autorizacion)

        self.assertIn("ESTADO SRI: AUTORIZADO", texto)
        self.assertIn("RECEPCION", texto)
        self.assertIn("AUTORIZACION", texto)
        self.assertIn("1234567890", texto)


class ClaveRegistradaTest(unittest.TestCase):
    def test_detecta_identificador_43(self):
        recepcion = {
            "estado": "DEVUELTA",
            "mensajes": [
                {
                    "identificador": "43",
                    "mensaje": "CLAVE ACCESO REGISTRADA",
                    "informacionAdicional": "",
                    "tipo": "ERROR",
                }
            ],
        }
        self.assertTrue(_tiene_error_clave_registrada(recepcion))

    def test_detecta_texto_de_clave_registrada(self):
        recepcion = {
            "estado": "DEVUELTA",
            "mensajes": [
                {
                    "identificador": "",
                    "mensaje": "La clave acceso registrada ya existe",
                    "informacionAdicional": "",
                    "tipo": "ERROR",
                }
            ],
        }
        self.assertTrue(_tiene_error_clave_registrada(recepcion))

    def test_no_confunde_otros_errores(self):
        recepcion = {
            "estado": "DEVUELTA",
            "mensajes": [
                {
                    "identificador": "35",
                    "mensaje": "SECUENCIAL REGISTRADO",
                    "informacionAdicional": "",
                    "tipo": "ERROR",
                }
            ],
        }
        self.assertFalse(_tiene_error_clave_registrada(recepcion))


class DuplicateAccessKeyTest(unittest.TestCase):
    def test_error_43_recupera_autorizacion_existente(self):
        with tempfile.TemporaryDirectory() as tmp:
            xml_path = Path(tmp) / "factura.xml"
            xml_path.write_text(
                f"<factura><infoTributaria><claveAcceso>{CLAVE}"
                "</claveAcceso></infoTributaria></factura>",
                encoding="utf-8",
            )

            recepcion = {
                "estado": "DEVUELTA",
                "mensajes": [
                    {
                        "identificador": "43",
                        "mensaje": "CLAVE ACCESO REGISTRADA",
                        "informacionAdicional": "",
                        "tipo": "ERROR",
                    }
                ],
                "clave_acceso": CLAVE,
                "raw": "<respuesta/>",
            }
            autorizacion = {
                "estado": "AUTORIZADO",
                "mensajes": [],
                "numero": "1234567890",
                "fecha": "2026-10-24T20:00:00-05:00",
                "comprobante": "",
                "raw": "<autorizacion/>",
            }

            with patch.object(
                sri_service, "_firmar_xml", return_value=(True, str(xml_path))
            ), patch.object(
                sri_service, "_enviar_recepcion", return_value=(True, recepcion)
            ), patch.object(
                sri_service,
                "_consultar_autorizacion",
                return_value=(True, autorizacion),
            ):
                ok, result = send_invoice(
                    str(xml_path),
                    {
                        "ambiente_sri": 1,
                        "firma_path": "/tmp/firma.p12",
                        "firma_pass": "",
                    },
                )

        self.assertTrue(ok)
        self.assertEqual(result["estado"], "AUTORIZADO")
        self.assertEqual(result["numero_autorizacion"], "1234567890")
        self.assertEqual(result["recepcion"]["estado"], "YA REGISTRADA")
        self.assertIn("ya estaba registrada", result["respuesta"])


if __name__ == "__main__":
    unittest.main()
