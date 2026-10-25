"""Envío de comprobantes electrónicos al SRI.

Implementa el flujo de recepción y autorización de los web services del SRI
para el ambiente de pruebas (``ambiente_sri = 1``) y producción (``2``).

El XML se firma con XAdES-BES usando el certificado .p12 configurado en
Mi Empresa. La firma se genera con SHA-1 porque es el algoritmo que exige
la ficha técnica del SRI para comprobantes electrónicos.
"""

from __future__ import annotations

import base64
import hashlib
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import requests

from core.logger import get_logger
from core.paths import GENERATED_DIR

logger = get_logger("SRIService")

SRI_ENDPOINTS = {
    1: {
        "recepcion": (
            "https://celcer.sri.gob.ec/comprobantes-electronicos-ws/"
            "RecepcionComprobantesOffline"
        ),
        "autorizacion": (
            "https://celcer.sri.gob.ec/comprobantes-electronicos-ws/"
            "AutorizacionComprobantesOffline"
        ),
        "nombre": "PRUEBAS",
    },
    2: {
        "recepcion": (
            "https://cel.sri.gob.ec/comprobantes-electronicos-ws/"
            "RecepcionComprobantesOffline"
        ),
        "autorizacion": (
            "https://cel.sri.gob.ec/comprobantes-electronicos-ws/"
            "AutorizacionComprobantesOffline"
        ),
        "nombre": "PRODUCCION",
    },
}

REQUEST_TIMEOUT = 40
AUTORIZACION_INTENTOS = 6
AUTORIZACION_ESPERA = 1.5


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _find_first(node, name: str):
    """Busca el primer descendiente por nombre local, sin depender del namespace."""
    for child in node.iter():
        if child is node:
            continue
        if _local_name(child.tag) == name:
            return child
    return None


def _find_all(node, name: str) -> list:
    return [child for child in node.iter() if _local_name(child.tag) == name]


def _text(node, name: str, default: str = "") -> str:
    found = _find_first(node, name)
    return (found.text or "").strip() if found is not None else default


def _parse_mensajes(container) -> list[dict]:
    mensajes = []
    if container is None:
        return mensajes
    for nodo in _find_all(container, "mensaje"):
        # El SRI anida un <mensaje> dentro de otro <mensaje>; solo el exterior
        # contiene los campos identificador/mensaje/informacionAdicional/tipo.
        if not any(
            _local_name(child.tag) == "identificador"
            for child in list(nodo)
        ):
            continue
        mensajes.append({
            "identificador": _text(nodo, "identificador"),
            "mensaje": _text(nodo, "mensaje"),
            "informacionAdicional": _text(nodo, "informacionAdicional"),
            "tipo": _text(nodo, "tipo"),
        })
    return mensajes


def _formatear_mensajes(mensajes: list[dict]) -> str:
    lineas = []
    for msg in mensajes:
        tipo = msg.get("tipo") or "INFO"
        identificador = msg.get("identificador") or ""
        detalle = msg.get("mensaje") or ""
        extra = msg.get("informacionAdicional") or ""
        cabecera = f"[{tipo}]"
        if identificador:
            cabecera += f" {identificador}"
        linea = f"{cabecera} {detalle}".strip()
        if extra:
            linea += f" - {extra}"
        lineas.append(linea)
    return "\n".join(lineas)


def _tiene_error_clave_registrada(recepcion: dict) -> bool:
    """Detecta el error 43 del SRI: la clave de acceso ya está registrada.

    Ocurre cuando se intenta reenviar un comprobante que ya fue recibido por
    el SRI. En ese caso no se debe tratar como un rechazo definitivo: hay que
    consultar la autorización existente.
    """
    for msg in recepcion.get("mensajes") or []:
        identificador = str(msg.get("identificador") or "").strip()
        texto = " ".join(
            str(msg.get(campo) or "")
            for campo in ("mensaje", "informacionAdicional")
        ).upper()
        if identificador == "43" or "CLAVE ACCESO REGISTRADA" in texto:
            return True
    return False


def _formatear_respuesta(estado: str, recepcion: dict, autorizacion: dict | None) -> str:
    lineas = [f"ESTADO SRI: {estado or 'SIN RESPUESTA'}"]

    if recepcion:
        lineas.append("")
        lineas.append("RECEPCION")
        lineas.append(f"Estado: {recepcion.get('estado') or 'N/A'}")
        if recepcion.get("nota"):
            lineas.append(recepcion["nota"])
        if recepcion.get("mensajes"):
            lineas.append(_formatear_mensajes(recepcion["mensajes"]))

    if autorizacion:
        lineas.append("")
        lineas.append("AUTORIZACION")
        lineas.append(f"Estado: {autorizacion.get('estado') or 'N/A'}")
        if autorizacion.get("numero"):
            lineas.append(f"Numero de autorizacion: {autorizacion['numero']}")
        if autorizacion.get("fecha"):
            lineas.append(f"Fecha de autorizacion: {autorizacion['fecha']}")
        if autorizacion.get("mensajes"):
            lineas.append(_formatear_mensajes(autorizacion["mensajes"]))

    return "\n".join(lineas).strip()


class _SRIXAdESSigner:
    """Fábrica diferida del firmador XAdES.

    Se importa ``signxml``/``lxml`` solo cuando se va a firmar. Así el resto de
    la aplicación puede funcionar aunque esas dependencias no estén instaladas
    (por ejemplo, en una compilación móvil sin soporte para SRI).
    """

    @staticmethod
    def create():
        from signxml.algorithms import (
            CanonicalizationMethod,
            DigestAlgorithm,
            SignatureConstructionMethod,
            SignatureMethod,
        )
        from signxml.xades import XAdESSigner

        class SRIXAdESSigner(XAdESSigner):
            # El SRI exige SHA-1; signxml lo bloquea por defecto por seguridad.
            def check_deprecated_methods(self):
                pass

            def add_signing_time(self, signed_signature_properties, sig_root, signing_settings):
                from lxml.etree import SubElement
                from signxml.util import xades_tag

                signing_time = SubElement(
                    signed_signature_properties,
                    xades_tag("SigningTime"),
                    nsmap=self.namespaces,
                )
                signing_time.text = datetime.now(
                    timezone(timedelta(hours=-5))
                ).isoformat(timespec="seconds")

            def add_signing_certificate(self, signed_signature_properties, sig_root, signing_settings):
                from base64 import b64encode

                from cryptography import x509
                from cryptography.hazmat.primitives.serialization import Encoding
                from lxml.etree import SubElement
                from signxml.algorithms import DigestAlgorithm
                from signxml.util import ds_tag, xades_tag

                signing_cert = SubElement(
                    signed_signature_properties,
                    xades_tag("SigningCertificate"),
                    nsmap=self.namespaces,
                )
                cert_chain = list(signing_settings.cert_chain or [])
                # El SRI solo espera el certificado del firmante.
                for cert in cert_chain[:1]:
                    loaded_cert = (
                        cert if isinstance(cert, x509.Certificate)
                        else x509.load_pem_x509_certificate(cert)
                    )
                    der = loaded_cert.public_bytes(Encoding.DER)
                    cert_node = SubElement(
                        signing_cert, xades_tag("Cert"), nsmap=self.namespaces
                    )
                    cert_digest = SubElement(
                        cert_node, xades_tag("CertDigest"), nsmap=self.namespaces
                    )
                    SubElement(
                        cert_digest,
                        ds_tag("DigestMethod"),
                        nsmap=self.namespaces,
                        Algorithm=DigestAlgorithm.SHA1.value,
                    )
                    SubElement(
                        cert_digest,
                        ds_tag("DigestValue"),
                        nsmap=self.namespaces,
                    ).text = b64encode(hashlib.sha1(der).digest()).decode()
                    issuer_serial = SubElement(
                        cert_node, xades_tag("IssuerSerial"), nsmap=self.namespaces
                    )
                    SubElement(
                        issuer_serial,
                        ds_tag("X509IssuerName"),
                        nsmap=self.namespaces,
                    ).text = loaded_cert.issuer.rfc4514_string()
                    SubElement(
                        issuer_serial,
                        ds_tag("X509SerialNumber"),
                        nsmap=self.namespaces,
                    ).text = str(loaded_cert.serial_number)

        return SRIXAdESSigner(
            method=SignatureConstructionMethod.enveloped,
            signature_algorithm=SignatureMethod.RSA_SHA1,
            digest_algorithm=DigestAlgorithm.SHA1,
            c14n_algorithm=CanonicalizationMethod.CANONICAL_XML_1_0,
        )


def _firmar_xml(xml_path: str, firma_path: str, firma_pass: str) -> tuple[bool, str]:
    """Firma el XML con XAdES-BES y devuelve ``(ok, ruta_firmada_o_error)``."""
    try:
        from cryptography.hazmat.primitives.serialization import pkcs12
        from lxml import etree
    except ImportError:
        return False, (
            "No están instaladas las dependencias de firma electrónica "
            "(signxml/lxml). Instálalas para enviar comprobantes al SRI."
        )

    xml_file = Path(str(xml_path or "")).expanduser()
    firma_file = Path(str(firma_path or "")).expanduser()
    if not xml_file.is_file():
        return False, "No se encontró el archivo XML de la factura."
    if not firma_file.is_file():
        return False, (
            "No se encontró el certificado de firma electrónica. "
            "Configúralo en Mi Empresa."
        )

    try:
        p12_data = firma_file.read_bytes()
        private_key, certificate, additional = pkcs12.load_key_and_certificates(
            p12_data, (firma_pass or "").encode("utf-8")
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo abrir el certificado .p12: %s", exc)
        return False, (
            "No se pudo abrir la firma electrónica. Verifica la contraseña "
            "del certificado en Mi Empresa."
        )

    if private_key is None or certificate is None:
        return False, "El certificado no contiene una clave privada válida."

    try:
        root = etree.parse(str(xml_file)).getroot()
        # Si el XML ya fue firmado, se reutiliza para no anidar firmas.
        if root.find(".//{http://www.w3.org/2000/09/xmldsig#}Signature") is not None:
            return True, str(xml_file)

        signer = _SRIXAdESSigner.create()
        cert_chain = [certificate] + list(additional or [])
        signed_root = signer.sign(
            root,
            key=private_key,
            cert=cert_chain,
            reference_uri="#comprobante",
            always_add_key_value=False,
        )
        signed_path = xml_file.with_name(f"{xml_file.stem}_firmado.xml")
        signed_path.write_bytes(
            etree.tostring(signed_root, xml_declaration=True, encoding="UTF-8")
        )
        return True, str(signed_path)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error firmando el XML de la factura")
        return False, f"No se pudo firmar el XML: {exc}"


def _post_soap(url: str, body: str) -> tuple[bool, str]:
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "",
    }
    try:
        response = requests.post(
            url,
            data=body.encode("utf-8"),
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Error conectando con el SRI (%s): %s", url, exc)
        return False, f"No se pudo conectar con el SRI: {exc}"

    if response.status_code != 200:
        return False, (
            f"El SRI respondió con HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )
    return True, response.text


def _enviar_recepcion(xml_content: bytes, endpoint: str) -> tuple[bool, dict | str]:
    xml_b64 = base64.b64encode(xml_content).decode("ascii")
    envelope = (
        '<soapenv:Envelope '
        'xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:ec="http://ec.gob.sri.ws.recepcion">'
        "<soapenv:Header/>"
        "<soapenv:Body><ec:validarComprobante>"
        f"<xml>{xml_b64}</xml>"
        "</ec:validarComprobante></soapenv:Body>"
        "</soapenv:Envelope>"
    )
    ok, response_text = _post_soap(endpoint, envelope)
    if not ok:
        return False, response_text

    try:
        root = ET.fromstring(response_text)
    except ET.ParseError as exc:
        return False, f"Respuesta inválida del SRI: {exc}"

    respuesta = _find_first(root, "RespuestaRecepcionComprobante")
    if respuesta is None:
        return False, f"Respuesta inesperada del SRI: {response_text[:500]}"

    estado = _text(respuesta, "estado")
    comprobante = _find_first(respuesta, "comprobante")
    mensajes = _parse_mensajes(comprobante)
    return True, {
        "estado": estado,
        "mensajes": mensajes,
        "clave_acceso": _text(comprobante, "claveAcceso"),
        "raw": response_text,
    }


def _consultar_autorizacion(clave_acceso: str, endpoint: str) -> tuple[bool, dict | str]:
    envelope = (
        '<soapenv:Envelope '
        'xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:ec="http://ec.gob.sri.ws.autorizacion">'
        "<soapenv:Header/>"
        "<soapenv:Body><ec:autorizacionComprobante>"
        f"<claveAccesoComprobante>{clave_acceso}</claveAccesoComprobante>"
        "</ec:autorizacionComprobante></soapenv:Body>"
        "</soapenv:Envelope>"
    )
    ok, response_text = _post_soap(endpoint, envelope)
    if not ok:
        return False, response_text

    try:
        root = ET.fromstring(response_text)
    except ET.ParseError as exc:
        return False, f"Respuesta inválida del SRI: {exc}"

    respuesta = _find_first(root, "RespuestaAutorizacionComprobante")
    if respuesta is None:
        return False, f"Respuesta inesperada del SRI: {response_text[:500]}"

    autorizacion = _find_first(respuesta, "autorizacion")
    if autorizacion is None:
        return True, {
            "estado": "EN PROCESO",
            "mensajes": [],
            "numero": "",
            "fecha": "",
            "comprobante": "",
            "raw": response_text,
        }

    return True, {
        "estado": _text(autorizacion, "estado"),
        "mensajes": _parse_mensajes(autorizacion),
        "numero": _text(autorizacion, "numeroAutorizacion"),
        "fecha": _text(autorizacion, "fechaAutorizacion"),
        "comprobante": _text(autorizacion, "comprobante"),
        "raw": response_text,
    }


def _guardar_xml_autorizado(clave_acceso: str, comprobante: str) -> str:
    """Guarda el XML autorizado que devuelve el SRI.

    El campo ``comprobante`` puede venir como XML plano (comportamiento
    observado en el ambiente de pruebas) o como base64. Se aceptan ambos
    formatos, incluido base64 sin relleno ``=``.
    """
    if not comprobante:
        return ""
    try:
        if isinstance(comprobante, bytes):
            contenido = comprobante
        else:
            texto = str(comprobante).strip().lstrip("\ufeff")
            if texto.startswith("<"):
                contenido = texto.encode("utf-8")
            else:
                compacto = "".join(texto.split())
                compacto += "=" * (-len(compacto) % 4)
                contenido = base64.b64decode(compacto)

        xml_dir = GENERATED_DIR / "invoices" / "xml"
        xml_dir.mkdir(parents=True, exist_ok=True)
        path = xml_dir / f"FAC_{clave_acceso}_autorizado.xml"
        path.write_bytes(contenido)
        return str(path)
    except Exception:  # noqa: BLE001
        logger.warning("No se pudo guardar el XML autorizado", exc_info=True)
        return ""


def send_invoice(xml_path: str, company_info: dict) -> tuple[bool, dict | str]:
    """Firma y envía una factura al SRI, consultando su autorización.

    Returns:
        ``(ok, resultado)``. ``ok`` es ``False`` solo ante errores de
        configuración, firma o conexión. Si el SRI respondió (aunque haya
        devuelto o rechazado el comprobante), ``ok`` es ``True`` y el
        resultado incluye el estado y los mensajes.
    """
    ambiente = int(company_info.get("ambiente_sri", 1) or 1)
    # El XML y el endpoint deben pertenecer al mismo ambiente. Si la empresa
    # cambió de ambiente después de generar la factura, manda el XML.
    try:
        xml_root = ET.fromstring(Path(str(xml_path)).read_bytes())
        ambiente_xml = int(_text(xml_root, "ambiente") or 0)
        if ambiente_xml in SRI_ENDPOINTS:
            ambiente = ambiente_xml
    except (OSError, ValueError, ET.ParseError):
        pass
    endpoints = SRI_ENDPOINTS.get(ambiente, SRI_ENDPOINTS[1])

    firma_path = str(company_info.get("firma_path") or "").strip()
    firma_pass = str(company_info.get("firma_pass") or "")
    if not firma_path:
        return False, (
            "No hay una firma electrónica configurada. "
            "Carga el certificado .p12 en Mi Empresa."
        )

    ok, signed_or_error = _firmar_xml(xml_path, firma_path, firma_pass)
    if not ok:
        return False, signed_or_error

    signed_path = signed_or_error
    try:
        xml_content = Path(signed_path).read_bytes()
    except OSError as exc:
        return False, f"No se pudo leer el XML firmado: {exc}"

    ok, recepcion = _enviar_recepcion(xml_content, endpoints["recepcion"])
    if not ok:
        return False, recepcion

    estado_recepcion = (recepcion.get("estado") or "").upper()
    autorizacion = None
    estado = estado_recepcion or "SIN RESPUESTA"
    clave = recepcion.get("clave_acceso") or ""

    if not clave:
        try:
            clave = _text(ET.fromstring(xml_content), "claveAcceso")
        except ET.ParseError:
            clave = ""

    # Si el SRI responde que la clave ya está registrada, el comprobante ya
    # fue enviado antes. Consultamos la autorización existente en lugar de
    # reportar un rechazo definitivo. Esto cubre los reintentos después de un
    # timeout o de un cierre inesperado durante la consulta de autorización.
    clave_ya_registrada = (
        estado_recepcion != "RECIBIDA"
        and _tiene_error_clave_registrada(recepcion)
    )

    if estado_recepcion == "RECIBIDA" or clave_ya_registrada:
        if len(clave) != 49:
            return True, {
                "estado": estado,
                "ambiente": endpoints["nombre"],
                "mensaje": "El SRI no devolvió una clave de acceso válida.",
                "respuesta": _formatear_respuesta(estado, recepcion, None),
                "recepcion": recepcion,
                "autorizacion": None,
                "clave_acceso": clave,
                "numero_autorizacion": "",
                "fecha_autorizacion": "",
                "xml_firmado_path": signed_path,
                "xml_autorizado_path": "",
                "respuesta_cruda": recepcion.get("raw", ""),
            }

        for intento in range(AUTORIZACION_INTENTOS):
            ok, autorizacion = _consultar_autorizacion(
                clave, endpoints["autorizacion"]
            )
            if not ok:
                return False, autorizacion
            estado_aut = (autorizacion.get("estado") or "").upper()
            estado = estado_aut or "EN PROCESO"
            if estado_aut != "EN PROCESO":
                break
            if intento < AUTORIZACION_INTENTOS - 1:
                time.sleep(AUTORIZACION_ESPERA)

        if clave_ya_registrada:
            if estado == "AUTORIZADO":
                nota = (
                    "La clave de acceso ya estaba registrada en el SRI; "
                    "se recuperó la autorización existente."
                )
            else:
                nota = (
                    "La clave de acceso ya estaba registrada en el SRI, "
                    "pero la consulta de autorización devolvió: "
                    f"{estado or 'SIN RESPUESTA'}."
                )
            recepcion = {
                "estado": "YA REGISTRADA",
                "mensajes": [],
                "nota": nota,
                "clave_acceso": clave,
            }

    mensaje = _formatear_respuesta(estado, recepcion, autorizacion)
    xml_autorizado = ""
    if autorizacion and (autorizacion.get("estado") or "").upper() == "AUTORIZADO":
        xml_autorizado = _guardar_xml_autorizado(
            clave or autorizacion.get("numero") or "",
            autorizacion.get("comprobante") or "",
        )

    return True, {
        "estado": estado,
        "ambiente": endpoints["nombre"],
        "mensaje": mensaje,
        "respuesta": _formatear_respuesta(estado, recepcion, autorizacion),
        "recepcion": recepcion,
        "autorizacion": autorizacion,
        "clave_acceso": recepcion.get("clave_acceso") or "",
        "numero_autorizacion": (autorizacion or {}).get("numero") or "",
        "fecha_autorizacion": (autorizacion or {}).get("fecha") or "",
        "xml_firmado_path": signed_path,
        "xml_autorizado_path": xml_autorizado,
        "respuesta_cruda": "\n\n".join(
            parte for parte in [
                recepcion.get("raw", ""),
                (autorizacion or {}).get("raw", ""),
            ] if parte
        ),
    }


class SRIService:
    """Fachada del servicio de comprobantes electrónicos del SRI."""

    send_invoice = staticmethod(send_invoice)
