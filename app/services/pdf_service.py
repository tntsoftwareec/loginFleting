import io
import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
)
from reportlab.graphics.barcode import code128
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

import qrcode

from core.paths import ASSETS_DIR, GENERATED_DIR

# ── Colores RIDE SRI ──────────────────────────────────────────────────────────
C_BORDER     = colors.HexColor('#000000')
C_LABEL_BG   = colors.HexColor('#EEEEEE')
C_TABLE_HEAD = colors.HexColor('#4472C4')
C_TABLE_ALT  = colors.HexColor('#EBF3FB')
C_TOTAL_BG   = colors.HexColor('#D9E2F3')
C_WHITE      = colors.white
C_BLUE_SRI   = colors.HexColor('#1F4E79')

PAGE_W = A4[0] - 3 * cm   # ancho util ~ 18.21 cm


def _quotation_image(image_path: str, max_width: float, max_height: float):
    """Devuelve un ``Image`` ajustado al espacio de la tabla o ``None``."""
    path = str(image_path or "").strip()
    if not path:
        return None

    try:
        from reportlab.lib.utils import ImageReader

        image_file = Path(path).expanduser()
        if not image_file.is_file():
            return None

        width, height = ImageReader(str(image_file)).getSize()
        if not width or not height:
            return None

        scale = min(max_width / float(width), max_height / float(height))
        return Image(
            str(image_file),
            width=float(width) * scale,
            height=float(height) * scale,
            hAlign='CENTER',
        )
    except Exception:  # noqa: BLE001
        # Una imagen dañada no debe impedir generar la cotización.
        return None


def _company_logo_image(company_info: dict):
    """Devuelve el logo configurado o el logo predeterminado de la app."""
    stored = str((company_info or {}).get("logo_path") or "").strip()
    candidates = []
    if stored:
        candidates.append(stored)
    candidates.extend([
        str(ASSETS_DIR / "logo.jpg"),
        str(ASSETS_DIR / "image.jpg"),
        str(ASSETS_DIR / "image.png"),
    ])

    seen = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        image = _quotation_image(candidate, 4 * cm, 1.6 * cm)
        if image:
            image.hAlign = 'LEFT'
            return image
    return None


class PDFService:
    @classmethod
    def generate_factura_pdf(
        cls,
        company_info: dict,
        invoice_data: dict,
        items: list,
        clave_acceso: str
    ) -> str:
        """Genera el RIDE PDF de la Factura Electronica conforme al estandar SRI Ecuador."""
        pdf_dir = GENERATED_DIR / "invoices" / "pdf"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_file = pdf_dir / f"FAC_{clave_acceso}.pdf"

        doc = SimpleDocTemplate(
            str(pdf_file),
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )

        styles = getSampleStyleSheet()

        def s(name, **kw):
            return ParagraphStyle(name, parent=styles['Normal'], **kw)

        st_company        = s('company',   fontSize=10, leading=12, fontName='Helvetica-Bold')
        st_body           = s('body',      fontSize=7.5, leading=10)
        st_body_c         = s('body_c',    fontSize=7.5, leading=10, alignment=TA_CENTER)
        st_label          = s('label',     fontSize=7.5, leading=10, fontName='Helvetica-Bold')
        st_label_c        = s('label_c',   fontSize=7.5, leading=10, fontName='Helvetica-Bold', alignment=TA_CENTER)
        st_doc_title      = s('doc_title', fontSize=13, leading=15, fontName='Helvetica-Bold', alignment=TA_CENTER, textColor=C_BLUE_SRI)
        st_th             = s('th',        fontSize=7.5, leading=9,  fontName='Helvetica-Bold', textColor=C_WHITE, alignment=TA_CENTER)
        st_td             = s('td',        fontSize=7.5, leading=9)
        st_td_c           = s('td_c',      fontSize=7.5, leading=9,  alignment=TA_CENTER)
        st_td_r           = s('td_r',      fontSize=7.5, leading=9,  alignment=TA_RIGHT)
        st_total_lbl      = s('total_lbl', fontSize=7.5, leading=9,  fontName='Helvetica-Bold')
        st_total_val      = s('total_val', fontSize=7.5, leading=9,  fontName='Helvetica-Bold', alignment=TA_RIGHT)
        st_vtotal_lbl     = s('vt_lbl',    fontSize=9,  leading=11, fontName='Helvetica-Bold', textColor=C_BLUE_SRI)
        st_vtotal_val     = s('vt_val',    fontSize=9,  leading=11, fontName='Helvetica-Bold', alignment=TA_RIGHT, textColor=C_BLUE_SRI)
        st_ca             = s('ca',        fontSize=6,  leading=7.5, alignment=TA_CENTER, textColor=colors.HexColor('#333333'))
        st_section        = s('section',   fontSize=8.5, leading=11, fontName='Helvetica-Bold', textColor=C_BLUE_SRI)

        elements = []

        # ══════════════════════════════════════════════════════════════════════
        # 1. CABECERA  ─  Emisor (izq) | RUC / FACTURA / No. / Autorizacion (der)
        # ══════════════════════════════════════════════════════════════════════
        razon_social     = company_info.get('razon_social', 'EMPRESA S.A.')
        nombre_comercial = company_info.get('nombre_comercial', razon_social)
        dir_matriz       = company_info.get('direccion_matriz', '')
        dir_estab        = company_info.get('direccion_establecimiento', dir_matriz)
        ruc              = company_info.get('ruc', '')
        contrib_esp      = (company_info.get('contribuyente_especial') or '').strip()
        obliga_cont      = company_info.get('obligado_contabilidad', 'NO')
        telefono         = company_info.get('telefono', '')
        email_emp        = company_info.get('email', '')
        amb_num          = int(company_info.get('ambiente_sri', 1))
        amb_str          = 'PRUEBAS' if amb_num == 1 else 'PRODUCCION'
        secuencial       = invoice_data.get('secuencial', '001-001-000000001')
        fecha_emision    = invoice_data.get('fecha_emision', '')

        # Logo personalizado de la empresa (con respaldo en el logo de la app)
        logo_img = _company_logo_image(company_info)

        # Cabecera sin tablas visibles: solo el logo y el texto del emisor.
        left_cell = []
        if logo_img:
            left_cell.extend([logo_img, Spacer(1, 2 * mm)])
        left_cell += [
            Paragraph(razon_social, st_company),
            Paragraph(f'<b>Nombre Comercial:</b> {nombre_comercial}', st_body),
            Paragraph(f'<b>Direccion Matriz:</b> {dir_matriz}', st_body),
            Paragraph(f'<b>Direccion Establecimiento:</b> {dir_estab}', st_body),
        ]
        if contrib_esp:
            left_cell.append(
                Paragraph(f'<b>Contribuyente Especial N.</b> {contrib_esp}', st_body)
            )
        left_cell += [
            Paragraph(f'<b>Obligado a llevar Contabilidad:</b> {obliga_cont}', st_body),
            Paragraph(f'<b>Telefono:</b> {telefono}   <b>Email:</b> {email_emp}', st_body),
        ]

        right_cell = [
            Paragraph(f'R.U.C.: {ruc}', st_label_c),
            Paragraph('FACTURA', st_doc_title),
            Paragraph(f'No. {secuencial}', st_label_c),
            Spacer(1, 2 * mm),
            Paragraph('NUMERO DE AUTORIZACION', st_label_c),
            Paragraph(clave_acceso, st_ca),
            Paragraph(f'<b>Fecha y Hora de Autorizacion:</b> {fecha_emision}', st_body_c),
            Paragraph(f'<b>Ambiente:</b> {amb_str}', st_body_c),
            Paragraph('<b>Emision:</b> NORMAL', st_body_c),
        ]

        header_tbl = Table(
            [[left_cell, right_cell]],
            colWidths=[PAGE_W * 0.55, PAGE_W * 0.45],
        )
        header_tbl.setStyle(TableStyle([
            ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING',  (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING',   (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_tbl)
        elements.append(Spacer(1, 3 * mm))

        # ══════════════════════════════════════════════════════════════════════
        # 2. DATOS DEL COMPRADOR
        # ══════════════════════════════════════════════════════════════════════
        client_name  = invoice_data.get('client_nombre', 'CONSUMIDOR FINAL')
        client_ident = invoice_data.get('client_identificacion', '9999999999999')
        client_dir   = invoice_data.get('client_direccion', 'Ciudad')
        client_email = invoice_data.get('client_email', '')
        forma_pago   = invoice_data.get('forma_pago', 'EFECTIVO')
        tipo_doc     = invoice_data.get('client_tipo_doc', 'CEDULA')

        elements.append(Paragraph('DATOS DEL COMPRADOR / CLIENTE', st_section))
        elements.append(Spacer(1, 1 * mm))

        c1 = PAGE_W * 0.22
        c2 = PAGE_W * 0.38
        c3 = PAGE_W * 0.18
        c4 = PAGE_W * 0.22

        # Código de barras con el número de identificación
        barcode_ident = Paragraph('', st_body)
        if client_ident:
            try:
                barcode_ident = code128.Code128(
                    client_ident,
                    barWidth=0.012 * cm,
                    barHeight=0.8 * cm,
                    humanReadable=False,
                )
            except Exception:
                barcode_ident = Paragraph('', st_body)

        buyer_rows = [
            [Paragraph('<b>Razon Social / Nombres:</b>', st_label),
             Paragraph(client_name, st_body),
             Paragraph('<b>Identificacion:</b>', st_label),
             barcode_ident],
            [Paragraph('', st_body),
             Paragraph('', st_body),
             Paragraph('', st_body),
             Paragraph(client_ident, st_body)],
            [Paragraph('<b>Direccion:</b>', st_label),
             Paragraph(client_dir, st_body),
             Paragraph('<b>Tipo Identificacion:</b>', st_label),
             Paragraph(tipo_doc, st_body)],
            [Paragraph('<b>Email:</b>', st_label),
             Paragraph(client_email, st_body),
             Paragraph('<b>Forma de Pago:</b>', st_label),
             Paragraph(forma_pago, st_body)],
        ]
        buyer_tbl = Table(buyer_rows, colWidths=[c1, c2, c3, c4])
        buyer_tbl.setStyle(TableStyle([
            ('BOX',       (0, 0), (-1, -1), 0.5, C_BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#CCCCCC')),
            ('PADDING',   (0, 0), (-1, -1), 4),
            ('VALIGN',    (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(buyer_tbl)
        elements.append(Spacer(1, 3 * mm))

        # ══════════════════════════════════════════════════════════════════════
        # 3. DETALLE DE PRODUCTOS / SERVICIOS
        # ══════════════════════════════════════════════════════════════════════
        cw = [
            PAGE_W * 0.10,
            PAGE_W * 0.08,
            PAGE_W * 0.06,
            PAGE_W * 0.07,
            PAGE_W * 0.31,
            PAGE_W * 0.12,
            PAGE_W * 0.11,
            PAGE_W * 0.15,
        ]
        detail_data = [[
            Paragraph('Cod.\nPrincipal', st_th),
            Paragraph('Cod.\nAuxiliar',  st_th),
            Paragraph('Cant.',           st_th),
            Paragraph('Unidad\nMedida',  st_th),
            Paragraph('Descripcion',     st_th),
            Paragraph('Precio\nUnitario', st_th),
            Paragraph('Descuento',       st_th),
            Paragraph('Precio Total\nS/Imp.', st_th),
        ]]
        for item in items:
            detail_data.append([
                Paragraph(str(item.get('codigo', '')),                    st_td),
                Paragraph('',                                              st_td),
                Paragraph(f"{float(item.get('cantidad', 1)):.2f}",        st_td_c),
                Paragraph('UNIDAD',                                        st_td_c),
                Paragraph(str(item.get('descripcion', '')),                st_td),
                Paragraph(f"${float(item.get('precio_unitario', 0)):.2f}", st_td_r),
                Paragraph(f"${float(item.get('descuento', 0)):.2f}",       st_td_r),
                Paragraph(f"${float(item.get('subtotal', 0)):.2f}",        st_td_r),
            ])

        detail_tbl = Table(detail_data, colWidths=cw, repeatRows=1)
        detail_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), C_TABLE_HEAD),
            ('TEXTCOLOR',     (0, 0), (-1, 0), C_WHITE),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX',           (0, 0), (-1, -1), 0.5, C_BORDER),
            ('INNERGRID',     (0, 0), (-1, -1), 0.3, colors.HexColor('#CCCCCC')),
            ('PADDING',       (0, 0), (-1, -1), 3),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [C_WHITE, C_TABLE_ALT]),
        ]))
        elements.append(detail_tbl)
        elements.append(Spacer(1, 3 * mm))

        # ══════════════════════════════════════════════════════════════════════
        # 4. INFORMACION ADICIONAL + QR  |  TOTALES
        # ══════════════════════════════════════════════════════════════════════
        tot_sin_imp = float(invoice_data.get('subtotal_sin_impuestos', 0))
        tot_0       = float(invoice_data.get('subtotal_0', 0))
        tot_15      = float(invoice_data.get('subtotal_15', 0))
        tot_desc    = float(invoice_data.get('total_descuento', 0))
        iva_val     = float(invoice_data.get('iva_total', 0))
        imp_total   = float(invoice_data.get('importe_total', 0))

        # QR
        qr_element = Paragraph('<b>[ QR ]</b>', st_body_c)
        try:
            qr = qrcode.QRCode(version=1, box_size=3, border=1)
            qr.add_data(clave_acceso)
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color='black', back_color='white')
            buf = io.BytesIO()
            img_qr.save(buf, format='PNG')
            buf.seek(0)
            qr_element = Image(buf, width=2.2 * cm, height=2.2 * cm)
        except Exception:
            pass

        # Info adicional
        info_rows = [
            [Paragraph('INFORMACION ADICIONAL', st_label_c)],
            [Paragraph(f'<b>Email cliente:</b> {client_email}', st_body)],
            [Paragraph(f'<b>Telefono empresa:</b> {telefono}', st_body)],
            [Paragraph('<b>Software:</b> TntPos', st_body)],
            [Paragraph(f'<b>Fecha emision:</b> {fecha_emision}', st_body)],
        ]
        info_tbl = Table(info_rows, colWidths=[PAGE_W * 0.40])
        info_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), C_LABEL_BG),
            ('BOX',        (0, 0), (-1, -1), 0.5, C_BORDER),
            ('LINEBELOW',  (0, 0), (0, 0), 0.5, C_BORDER),
            ('PADDING',    (0, 0), (-1, -1), 4),
        ]))

        left_bottom = Table(
            [[info_tbl], [Spacer(1, 2 * mm)], [qr_element]],
            colWidths=[PAGE_W * 0.40],
        )
        left_bottom.setStyle(TableStyle([
            ('ALIGN',  (0, 2), (0, 2), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        # Totales
        def tot_row(lbl, val, is_grand=False):
            ls = st_vtotal_lbl if is_grand else st_total_lbl
            vs = st_vtotal_val if is_grand else st_total_val
            return [Paragraph(lbl, ls), Paragraph(f'${val:.2f}', vs)]

        totals_data = [
            [Paragraph('RESUMEN DE VALORES', st_label_c), ''],
            tot_row('Subtotal sin Impuestos:', tot_sin_imp),
            tot_row('Subtotal IVA 0%:', tot_0),
            tot_row('Subtotal IVA 15%:', tot_15),
            tot_row('Total Descuentos:', tot_desc),
            tot_row('IVA 15%:', iva_val),
            tot_row('ICE:', 0.0),
            tot_row('VALOR TOTAL:', imp_total, is_grand=True),
        ]
        tw_lbl = PAGE_W * 0.32
        tw_val = PAGE_W * 0.18
        totals_tbl = Table(totals_data, colWidths=[tw_lbl, tw_val])
        totals_tbl.setStyle(TableStyle([
            ('SPAN',       (0, 0), (1, 0)),
            ('BACKGROUND', (0, 0), (1, 0), C_LABEL_BG),
            ('ALIGN',      (0, 0), (1, 0), 'CENTER'),
            ('BOX',        (0, 0), (-1, -1), 0.5, C_BORDER),
            ('INNERGRID',  (0, 1), (-1, -1), 0.3, colors.HexColor('#CCCCCC')),
            ('BACKGROUND', (0, -1), (-1, -1), C_TOTAL_BG),
            ('PADDING',    (0, 0), (-1, -1), 4),
            ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        sp = PAGE_W * 0.10
        bottom_tbl = Table(
            [[left_bottom, Spacer(sp, 1), totals_tbl]],
            colWidths=[PAGE_W * 0.40, sp, tw_lbl + tw_val],
        )
        bottom_tbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(bottom_tbl)
        elements.append(Spacer(1, 4 * mm))

        # ══════════════════════════════════════════════════════════════════════
        # 5. CODIGO DE BARRAS Code128 – ancho completo (vectorial, alta calidad SRI)
        # ══════════════════════════════════════════════════════════════════════
        barcode_el = Paragraph(f'<font size=6>{clave_acceso}</font>', st_ca)
        try:
            bar_width = 0.016 * cm
            bc = code128.Code128(
                clave_acceso,
                barWidth=bar_width,
                barHeight=1.2 * cm,
                humanReadable=False,
            )
            # Si el código es más ancho que la página, se reduce el ancho de barra
            if bc.width > PAGE_W:
                bc = code128.Code128(
                    clave_acceso,
                    barWidth=bar_width * (PAGE_W / bc.width),
                    barHeight=1.2 * cm,
                    humanReadable=False,
                )
            barcode_el = bc
        except Exception:
            pass

        bc_tbl = Table(
            [
                [Paragraph('<b>CLAVE DE ACCESO / NUMERO DE AUTORIZACION</b>', st_label_c)],
                [barcode_el],
                [Paragraph(clave_acceso, st_ca)],
            ],
            colWidths=[PAGE_W],
        )
        bc_tbl.setStyle(TableStyle([
            ('BOX',        (0, 0), (-1, -1), 0.5, C_BORDER),
            ('BACKGROUND', (0, 0), (0, 0), C_LABEL_BG),
            ('LINEBELOW',  (0, 0), (0, 0), 0.5, C_BORDER),
            ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING',    (0, 0), (-1, -1), 4),
        ]))
        elements.append(KeepTogether(bc_tbl))

        doc.build(elements)
        return str(pdf_file)

    @classmethod
    def generate_cotizacion_pdf(
        cls,
        company_info: dict,
        quotation_data: dict,
        items: list,
    ) -> str:
        """Genera el PDF de la Cotización / Proforma."""
        pdf_dir = GENERATED_DIR / "quotations" / "pdf"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        secuencial = quotation_data.get('secuencial', 'COT-000')
        safe_name = secuencial.replace("-", "_")
        pdf_file = pdf_dir / f"{safe_name}.pdf"
        # Se genera en un temporal y se reemplaza al final para no dejar un
        # PDF incompleto si falla una regeneración (p. ej. una imagen dañada).
        tmp_file = pdf_dir / f".{safe_name}.{os.getpid()}.tmp.pdf"

        doc = SimpleDocTemplate(
            str(tmp_file),
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )

        styles = getSampleStyleSheet()

        def s(name, **kw):
            return ParagraphStyle(name, parent=styles['Normal'], **kw)

        st_company    = s('q_company',   fontSize=10, leading=12, fontName='Helvetica-Bold')
        st_body       = s('q_body',      fontSize=7.5, leading=10)
        st_body_c     = s('q_body_c',    fontSize=7.5, leading=10, alignment=TA_CENTER)
        st_label      = s('q_label',     fontSize=7.5, leading=10, fontName='Helvetica-Bold')
        st_label_c    = s('q_label_c',   fontSize=7.5, leading=10, fontName='Helvetica-Bold', alignment=TA_CENTER)
        st_doc_title  = s('q_doc_title', fontSize=13, leading=15, fontName='Helvetica-Bold', alignment=TA_CENTER, textColor=colors.HexColor('#6D28D9'))
        st_th         = s('q_th',        fontSize=7.5, leading=9,  fontName='Helvetica-Bold', textColor=C_WHITE, alignment=TA_CENTER)
        st_td         = s('q_td',        fontSize=7.5, leading=9)
        st_td_c       = s('q_td_c',     fontSize=7.5, leading=9,  alignment=TA_CENTER)
        st_td_r       = s('q_td_r',     fontSize=7.5, leading=9,  alignment=TA_RIGHT)
        st_total_lbl  = s('q_total_lbl', fontSize=7.5, leading=9,  fontName='Helvetica-Bold')
        st_total_val  = s('q_total_val', fontSize=7.5, leading=9,  fontName='Helvetica-Bold', alignment=TA_RIGHT)
        st_vtotal_lbl = s('q_vt_lbl',   fontSize=9,  leading=11, fontName='Helvetica-Bold', textColor=colors.HexColor('#6D28D9'))
        st_vtotal_val = s('q_vt_val',   fontSize=9,  leading=11, fontName='Helvetica-Bold', alignment=TA_RIGHT, textColor=colors.HexColor('#6D28D9'))
        st_section    = s('q_section',  fontSize=8.5, leading=11, fontName='Helvetica-Bold', textColor=colors.HexColor('#6D28D9'))

        C_PURPLE_HEAD = colors.HexColor('#7C3AED')

        elements = []

        # ══════════════════════════════════════════════════════════════════════
        # 1. CABECERA
        # ══════════════════════════════════════════════════════════════════════
        razon_social     = company_info.get('razon_social', 'EMPRESA S.A.')
        nombre_comercial = company_info.get('nombre_comercial', razon_social)
        dir_matriz       = company_info.get('direccion_matriz', '')
        ruc              = company_info.get('ruc', '')
        telefono         = company_info.get('telefono', '')
        email_emp        = company_info.get('email', '')
        fecha_emision    = quotation_data.get('fecha_emision', '')
        fecha_validez    = quotation_data.get('fecha_validez', '')

        # Logo personalizado de la empresa (con respaldo en el logo de la app)
        logo_img = _company_logo_image(company_info)

        # Cabecera sin tablas visibles: solo el logo y el texto del emisor.
        left_cell = []
        if logo_img:
            left_cell.extend([logo_img, Spacer(1, 2 * mm)])
        left_cell += [
            Paragraph(razon_social, st_company),
            Paragraph(f'<b>Nombre Comercial:</b> {nombre_comercial}', st_body),
            Paragraph(f'<b>Direccion:</b> {dir_matriz}', st_body),
            Paragraph(f'<b>RUC:</b> {ruc}', st_body),
            Paragraph(f'<b>Telefono:</b> {telefono}   <b>Email:</b> {email_emp}', st_body),
        ]

        right_cell = [
            Paragraph('COTIZACIÓN', st_doc_title),
            Paragraph(f'N° {secuencial}', st_label_c),
            Paragraph(f'<b>Fecha Emisión:</b> {fecha_emision}', st_body_c),
            Paragraph(f'<b>Válida hasta:</b> {fecha_validez}', st_body_c),
        ]

        header_tbl = Table(
            [[left_cell, right_cell]],
            colWidths=[PAGE_W * 0.55, PAGE_W * 0.45],
        )
        header_tbl.setStyle(TableStyle([
            ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING',  (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING',   (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_tbl)
        elements.append(Spacer(1, 3 * mm))

        # ══════════════════════════════════════════════════════════════════════
        # 2. DATOS DEL CLIENTE
        # ══════════════════════════════════════════════════════════════════════
        client_name  = quotation_data.get('client_nombre', 'CLIENTE')
        client_ident = quotation_data.get('client_identificacion', '')
        client_dir   = quotation_data.get('client_direccion', 'Ciudad')
        client_email = quotation_data.get('client_email', '')

        elements.append(Paragraph('DATOS DEL CLIENTE', st_section))
        elements.append(Spacer(1, 1 * mm))

        c1 = PAGE_W * 0.22
        c2 = PAGE_W * 0.38
        c3 = PAGE_W * 0.18
        c4 = PAGE_W * 0.22

        buyer_rows = [
            [Paragraph('<b>Razon Social / Nombres:</b>', st_label),
             Paragraph(client_name, st_body),
             Paragraph('<b>Identificacion:</b>', st_label),
             Paragraph(client_ident, st_body)],
            [Paragraph('<b>Direccion:</b>', st_label),
             Paragraph(client_dir, st_body),
             Paragraph('<b>Email:</b>', st_label),
             Paragraph(client_email, st_body)],
        ]
        buyer_tbl = Table(buyer_rows, colWidths=[c1, c2, c3, c4])
        buyer_tbl.setStyle(TableStyle([
            ('BOX',       (0, 0), (-1, -1), 0.5, C_BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#CCCCCC')),
            ('PADDING',   (0, 0), (-1, -1), 4),
            ('VALIGN',    (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(buyer_tbl)
        elements.append(Spacer(1, 3 * mm))

        # ══════════════════════════════════════════════════════════════════════
        # 3. DETALLE DE PRODUCTOS / SERVICIOS
        # ══════════════════════════════════════════════════════════════════════
        cw = [
            PAGE_W * 0.10,   # Imagen
            PAGE_W * 0.09,   # Código
            PAGE_W * 0.06,   # Cantidad
            PAGE_W * 0.31,   # Descripción
            PAGE_W * 0.12,   # Precio unitario
            PAGE_W * 0.10,   # Descuento
            PAGE_W * 0.07,   # IVA
            PAGE_W * 0.15,   # Total
        ]
        detail_data = [[
            Paragraph('Imagen', st_th),
            Paragraph('Código', st_th),
            Paragraph('Cant.', st_th),
            Paragraph('Descripción', st_th),
            Paragraph('P. Unitario', st_th),
            Paragraph('Descuento', st_th),
            Paragraph('IVA %', st_th),
            Paragraph('Total', st_th),
        ]]
        for item in items:
            product_image = _quotation_image(
                item.get('imagen_path', ''),
                1.45 * cm,
                1.45 * cm,
            )
            detail_data.append([
                product_image or Paragraph('—', st_td_c),
                Paragraph(str(item.get('codigo', '')), st_td),
                Paragraph(f"{float(item.get('cantidad', 1)):.2f}", st_td_c),
                Paragraph(str(item.get('descripcion', '')), st_td),
                Paragraph(f"${float(item.get('precio_unitario', 0)):.2f}", st_td_r),
                Paragraph(f"${float(item.get('descuento', 0)):.2f}", st_td_r),
                Paragraph(f"{float(item.get('iva_porcentaje', 15)):.0f}%", st_td_c),
                Paragraph(f"${float(item.get('total', 0)):.2f}", st_td_r),
            ])

        detail_tbl = Table(detail_data, colWidths=cw, repeatRows=1)
        detail_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), C_PURPLE_HEAD),
            ('TEXTCOLOR',     (0, 0), (-1, 0), C_WHITE),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX',           (0, 0), (-1, -1), 0.5, C_BORDER),
            ('INNERGRID',     (0, 0), (-1, -1), 0.3, colors.HexColor('#CCCCCC')),
            ('PADDING',       (0, 0), (-1, -1), 3),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [C_WHITE, C_TABLE_ALT]),
        ]))
        elements.append(detail_tbl)
        elements.append(Spacer(1, 3 * mm))

        # ══════════════════════════════════════════════════════════════════════
        # 4. NOTAS + TOTALES
        # ══════════════════════════════════════════════════════════════════════
        tot_sin_imp = float(quotation_data.get('subtotal_sin_impuestos', 0))
        tot_0       = float(quotation_data.get('subtotal_0', 0))
        tot_15      = float(quotation_data.get('subtotal_15', 0))
        tot_desc    = float(quotation_data.get('total_descuento', 0))
        iva_val     = float(quotation_data.get('iva_total', 0))
        imp_total   = float(quotation_data.get('importe_total', 0))
        notas       = quotation_data.get('notas', '')

        # Notas
        notas_rows = [
            [Paragraph('NOTAS / OBSERVACIONES', st_label_c)],
            [Paragraph(notas if notas else '—', st_body)],
            [Paragraph(f'<b>Documento válido hasta:</b> {fecha_validez}', st_body)],
        ]
        notas_tbl = Table(notas_rows, colWidths=[PAGE_W * 0.44])
        notas_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), C_LABEL_BG),
            ('BOX',        (0, 0), (-1, -1), 0.5, C_BORDER),
            ('LINEBELOW',  (0, 0), (0, 0), 0.5, C_BORDER),
            ('PADDING',    (0, 0), (-1, -1), 4),
        ]))
        elements.append(notas_tbl)
        elements.append(Spacer(1, 3 * mm))

        # Totales
        def tot_row(lbl, val, is_grand=False):
            ls = st_vtotal_lbl if is_grand else st_total_lbl
            vs = st_vtotal_val if is_grand else st_total_val
            return [Paragraph(lbl, ls), Paragraph(f'${val:.2f}', vs)]

        totals_data = [
            [Paragraph('RESUMEN DE VALORES', st_label_c), ''],
            tot_row('Subtotal sin Impuestos:', tot_sin_imp),
            tot_row('Subtotal IVA 0%:', tot_0),
            tot_row('Subtotal IVA 15%:', tot_15),
            tot_row('Total Descuentos:', tot_desc),
            tot_row('IVA 15%:', iva_val),
            tot_row('VALOR TOTAL:', imp_total, is_grand=True),
        ]
        tw_lbl = PAGE_W * 0.30
        tw_val = PAGE_W * 0.20
        totals_tbl = Table(totals_data, colWidths=[tw_lbl, tw_val], hAlign='RIGHT')
        totals_tbl.setStyle(TableStyle([
            ('SPAN',       (0, 0), (1, 0)),
            ('BACKGROUND', (0, 0), (1, 0), C_LABEL_BG),
            ('ALIGN',      (0, 0), (1, 0), 'CENTER'),
            ('BOX',        (0, 0), (-1, -1), 0.5, C_BORDER),
            ('INNERGRID',  (0, 1), (-1, -1), 0.3, colors.HexColor('#CCCCCC')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#EDE9FE')),
            ('PADDING',    (0, 0), (-1, -1), 4),
            ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(totals_tbl)
        elements.append(Spacer(1, 6 * mm))

        # ══════════════════════════════════════════════════════════════════════
        # 5. PIE — Leyenda
        # ══════════════════════════════════════════════════════════════════════
        st_footer = s('q_footer', fontSize=7, leading=9, alignment=TA_CENTER, textColor=colors.HexColor('#888888'))
        footer_tbl = Table(
            [
                [Paragraph('Este documento es una cotización / proforma y no tiene validez tributaria.', st_footer)],
                [Paragraph(f'Generado por {company_info.get("nombre_comercial", razon_social)} — TntPos', st_footer)],
            ],
            colWidths=[PAGE_W],
        )
        footer_tbl.setStyle(TableStyle([
            ('BOX',     (0, 0), (-1, -1), 0.3, colors.HexColor('#CCCCCC')),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(footer_tbl)

        try:
            doc.build(elements)
            os.replace(tmp_file, pdf_file)
        except Exception:
            try:
                tmp_file.unlink()
            except OSError:
                pass
            raise
        return str(pdf_file)
