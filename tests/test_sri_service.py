import unittest
from xml.etree import ElementTree as ET

from tests.base import ensure_faker

ensure_faker()

from app.services.sri_service import (
    _find_first,
    _formatear_respuesta,
    _parse_mensajes,
)


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


if __name__ == "__main__":
    unittest.main()
