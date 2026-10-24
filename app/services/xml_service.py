import os
import random
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path

from core.paths import GENERATED_DIR

class XMLService:
    @staticmethod
    def generate_clave_acceso(fecha_dt: datetime, tipo_comprobante: str, ruc: str, ambiente: int, estab: str, pto_emi: str, secuencial: str):
        """Genera la clave de acceso de 49 dígitos para el SRI Ecuador.
        Format:
        1. Fecha de Emisión (8 d) ddmmaaaa
        2. Tipo de Comprobante (2 d) 01=Factura
        3. Número de RUC (13 d)
        4. Tipo de Ambiente (1 d) 1=Pruebas, 2=Producción
        5. Serie (6 d) estab (3d) + ptoEmi (3d)
        6. Número Comprobante (9 d) secuencial
        7. Código Numérico (8 d) numérico aleatorio
        8. Tipo de Emisión (1 d) 1=Normal
        9. Módulo 11 (1 d) dígito verificador
        """
        fecha_str = fecha_dt.strftime("%d%m%Y")
        cod_doc = tipo_comprobante.zfill(2)
        ruc_13 = ruc.zfill(13)
        amb = str(ambiente)
        serie = f"{estab.zfill(3)}{pto_emi.zfill(3)}"
        sec_9 = secuencial.zfill(9)
        codigo_num = f"{random.randint(10000000, 99999999)}"
        tipo_emi = "1"

        key48 = f"{fecha_str}{cod_doc}{ruc_13}{amb}{serie}{sec_9}{codigo_num}{tipo_emi}"
        
        # Módulo 11 calculation
        verificador = XMLService._calcular_modulo11(key48)
        return f"{key48}{verificador}"

    @staticmethod
    def _calcular_modulo11(cadena: str) -> int:
        pivot = 2
        suma = 0
        for i in range(len(cadena) - 1, -1, -1):
            suma += int(cadena[i]) * pivot
            pivot += 1
            if pivot > 7:
                pivot = 2
        resto = suma % 11
        dv = 11 - resto
        if dv == 11:
            return 0
        elif dv == 10:
            return 1
        return dv

    @staticmethod
    def get_tipo_identificacion_sri(tipo_doc: str, identificacion: str) -> str:
        """Mapea el tipo de identificación al código SRI."""
        t = (tipo_doc or "").upper()
        if identificacion == "9999999999999":
            return "07"  # Consumidor final
        if "RUC" in t or len(identificacion) == 13:
            return "04"
        if "CEDULA" in t or "CÉDULA" in t or len(identificacion) == 10:
            return "05"
        if "PASAPORTE" in t:
            return "06"
        return "07"

    @classmethod
    def create_factura_xml(cls, company_info: dict, invoice_data: dict, items: list) -> tuple:
        """Crea el documento XML de la factura según especificaciones SRI.
        
        Returns:
            (xml_path: str, xml_content: str, clave_acceso: str)
        """
        fecha_dt = datetime.strptime(invoice_data["fecha_emision"], "%Y-%m-%d")
        sec_str = str(invoice_data["secuencial"]).split("-")[-1] if "-" in str(invoice_data["secuencial"]) else str(invoice_data["secuencial"]).zfill(9)

        clave_acceso = invoice_data.get("clave_acceso")
        if not clave_acceso or len(clave_acceso) != 49:
            clave_acceso = cls.generate_clave_acceso(
                fecha_dt=fecha_dt,
                tipo_comprobante="01",
                ruc=company_info.get("ruc", "1790000000001"),
                ambiente=int(company_info.get("ambiente_sri", 1)),
                estab=company_info.get("establecimiento", "001"),
                pto_emi=company_info.get("punto_emision", "001"),
                secuencial=sec_str
            )

        root = ET.Element("factura", id="comprobante", version="1.1.0")

        # --- InfoTributaria ---
        info_trib = ET.SubElement(root, "infoTributaria")
        ET.SubElement(info_trib, "ambiente").text = str(company_info.get("ambiente_sri", 1))
        ET.SubElement(info_trib, "tipoEmision").text = "1"
        ET.SubElement(info_trib, "razonSocial").text = company_info.get("razon_social", "MI EMPRESA S.A.")
        ET.SubElement(info_trib, "nombreComercial").text = company_info.get("nombre_comercial", "MI NEGOCIO")
        ET.SubElement(info_trib, "ruc").text = company_info.get("ruc", "1790000000001")
        ET.SubElement(info_trib, "claveAcceso").text = clave_acceso
        ET.SubElement(info_trib, "codDoc").text = "01"
        ET.SubElement(info_trib, "estab").text = str(company_info.get("establecimiento", "001")).zfill(3)
        ET.SubElement(info_trib, "ptoEmi").text = str(company_info.get("punto_emision", "001")).zfill(3)
        ET.SubElement(info_trib, "secuencial").text = sec_str.zfill(9)
        ET.SubElement(info_trib, "dirMatriz").text = company_info.get("direccion_matriz", "Dirección Principal")

        # --- InfoFactura ---
        info_fac = ET.SubElement(root, "infoFactura")
        ET.SubElement(info_fac, "fechaEmision").text = fecha_dt.strftime("%d/%m/%Y")
        ET.SubElement(info_fac, "dirEstablecimiento").text = company_info.get("direccion_matriz", "Dirección Principal")
        if company_info.get("contribuyente_especial"):
            ET.SubElement(info_fac, "contribuyenteEspecial").text = company_info.get("contribuyente_especial")
        ET.SubElement(info_fac, "obligadoContabilidad").text = company_info.get("obligado_contabilidad", "NO").upper()
        
        tipo_ident = cls.get_tipo_identificacion_sri(
            invoice_data.get("client_tipo_doc", ""),
            invoice_data.get("client_identificacion", "")
        )
        ET.SubElement(info_fac, "tipoIdentificacionComprador").text = tipo_ident
        ET.SubElement(info_fac, "razonSocialComprador").text = invoice_data.get("client_nombre", "CONSUMIDOR FINAL")
        ET.SubElement(info_fac, "identificacionComprador").text = invoice_data.get("client_identificacion", "9999999999999")
        ET.SubElement(info_fac, "direccionComprador").text = invoice_data.get("client_direccion", "Ciudad")
        ET.SubElement(info_fac, "totalSinImpuestos").text = f"{invoice_data.get('subtotal_sin_impuestos', 0.0):.2f}"
        ET.SubElement(info_fac, "totalDescuento").text = f"{invoice_data.get('total_descuento', 0.0):.2f}"

        # TotalConImpuestos
        tot_imp = ET.SubElement(info_fac, "totalConImpuestos")
        
        # Impuesto IVA 15% (o tarifa aplicada)
        if invoice_data.get("subtotal_15", 0) > 0:
            imp15 = ET.SubElement(tot_imp, "totalImpuesto")
            ET.SubElement(imp15, "codigo").text = "2"
            ET.SubElement(imp15, "codigoPorcentaje").text = "4"  # 15% SRI
            ET.SubElement(imp15, "baseImponible").text = f"{invoice_data.get('subtotal_15', 0.0):.2f}"
            ET.SubElement(imp15, "valor").text = f"{invoice_data.get('iva_total', 0.0):.2f}"
            
        if invoice_data.get("subtotal_0", 0) > 0 or invoice_data.get("subtotal_15", 0) == 0:
            imp0 = ET.SubElement(tot_imp, "totalImpuesto")
            ET.SubElement(imp0, "codigo").text = "2"
            ET.SubElement(imp0, "codigoPorcentaje").text = "0"  # 0% SRI
            ET.SubElement(imp0, "baseImponible").text = f"{invoice_data.get('subtotal_0', 0.0):.2f}"
            ET.SubElement(imp0, "valor").text = "0.00"

        ET.SubElement(info_fac, "propina").text = "0.00"
        ET.SubElement(info_fac, "importeTotal").text = f"{invoice_data.get('importe_total', 0.0):.2f}"
        ET.SubElement(info_fac, "moneda").text = "DOLAR"

        # Pagos
        pagos = ET.SubElement(info_fac, "pagos")
        pago = ET.SubElement(pagos, "pago")
        # Codigo 01 = Sin utilización del sistema financiero (Efectivo), 20 = Otros
        forma = invoice_data.get("forma_pago", "EFECTIVO").upper()
        cod_pago = "01" if "EFECTIVO" in forma else "20"
        ET.SubElement(pago, "formaPago").text = cod_pago
        ET.SubElement(pago, "total").text = f"{invoice_data.get('importe_total', 0.0):.2f}"

        # --- Detalles ---
        detalles = ET.SubElement(root, "detalles")
        for item in items:
            det = ET.SubElement(detalles, "detalle")
            ET.SubElement(det, "codigoPrincipal").text = item.get("codigo", "SERV-001")
            ET.SubElement(det, "descripcion").text = item.get("descripcion", "Item")
            ET.SubElement(det, "cantidad").text = f"{item.get('cantidad', 1):.2f}"
            ET.SubElement(det, "precioUnitario").text = f"{item.get('precio_unitario', 0.0):.2f}"
            ET.SubElement(det, "descuento").text = f"{item.get('descuento', 0.0):.2f}"
            ET.SubElement(det, "precioTotalSinImpuesto").text = f"{item.get('subtotal', 0.0):.2f}"

            imps = ET.SubElement(det, "impuestos")
            imp = ET.SubElement(imps, "impuesto")
            ET.SubElement(imp, "codigo").text = "2"
            iva_p = float(item.get("iva_porcentaje", 15.0))
            ET.SubElement(imp, "codigoPorcentaje").text = "4" if iva_p > 0 else "0"
            ET.SubElement(imp, "tarifa").text = f"{iva_p:.2f}"
            ET.SubElement(imp, "baseImponible").text = f"{item.get('subtotal', 0.0):.2f}"
            ET.SubElement(imp, "valor").text = f"{item.get('valor_iva', 0.0):.2f}"

        # Formatting XML string
        xml_bytes = ET.tostring(root, encoding="utf-8")
        parsed = minidom.parseString(xml_bytes)
        xml_pretty = parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

        # Save to assets/invoices/xml/
        xml_dir = GENERATED_DIR / "invoices" / "xml"
        xml_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"FAC_{clave_acceso}.xml"
        file_path = xml_dir / file_name

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_pretty)

        return str(file_path), xml_pretty, clave_acceso
