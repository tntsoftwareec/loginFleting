import os
import io
from pathlib import Path
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

import qrcode

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class PDFService:
    @classmethod
    def generate_factura_pdf(cls, company_info: dict, invoice_data: dict, items: list, clave_acceso: str) -> str:
        """Genera el documento PDF RIDE de la Factura Electrónica.
        
        Returns:
            pdf_path: str
        """
        pdf_dir = BASE_DIR / "assets" / "invoices" / "pdf"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_file = pdf_dir / f"FAC_{clave_acceso}.pdf"

        doc = SimpleDocTemplate(
            str(pdf_file),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CompanyTitle',
            parent=styles['Heading1'],
            fontSize=14,
            leading=16,
            textColor=colors.HexColor('#1e293b'),
            fontName='Helvetica-Bold'
        )

        subtitle_style = ParagraphStyle(
            'CompanySub',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#475569')
        )

        box_title = ParagraphStyle(
            'BoxTitle',
            parent=styles['Heading2'],
            fontSize=11,
            leading=13,
            textColor=colors.HexColor('#0f172a'),
            fontName='Helvetica-Bold'
        )

        box_text = ParagraphStyle(
            'BoxText',
            parent=styles['Normal'],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#334155')
        )

        table_header = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.white,
            fontName='Helvetica-Bold',
            alignment=1
        )

        table_cell = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#1e293b')
        )

        table_cell_num = ParagraphStyle(
            'TableCellNum',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#1e293b'),
            alignment=2
        )

        elements = []

        # --- HEADER SECTION (Two Columns: Company vs Invoice Header Box) ---
        razon_social = company_info.get("razon_social", "MI EMPRESA S.A.")
        nombre_comercial = company_info.get("nombre_comercial", "MI NEGOCIO")
        dir_matriz = company_info.get("direccion_matriz", "Av. Principal 123")
        ruc = company_info.get("ruc", "1790000000001")
        contrib_esp = company_info.get("contribuyente_especial", "NO")
        obliga_cont = company_info.get("obligado_contabilidad", "NO")

        comp_text = f"""
        <b>{razon_social}</b><br/>
        <b>Nombre Comercial:</b> {nombre_comercial}<br/>
        <b>Matriz:</b> {dir_matriz}<br/>
        <b>Obligado a llevar Contabilidad:</b> {obliga_cont}<br/>
        {f'<b>Contribuyente Especial N°:</b> {contrib_esp}<br/>' if contrib_esp else ''}
        <b>Teléfono:</b> {company_info.get('telefono', '')}<br/>
        <b>Email:</b> {company_info.get('email', '')}
        """

        amb_str = "PRUEBAS" if int(company_info.get("ambiente_sri", 1)) == 1 else "PRODUCCIÓN"
        secuencial = invoice_data.get("secuencial", "001-001-000000001")

        inv_box_text = f"""
        <font color="#0f172a" size="11"><b>R.U.C.: {ruc}</b></font><br/>
        <font color="#2563eb" size="12"><b>FACTURA</b></font><br/>
        <b>No.: {secuencial}</b><br/>
        <b>NÚMERO DE AUTORIZACIÓN:</b><br/>
        <font size="6.5">{clave_acceso}</font><br/><br/>
        <b>FECHA Y HORA DE EMISIÓN:</b> {invoice_data.get('fecha_emision')}<br/>
        <b>AMBIENTE:</b> {amb_str}<br/>
        <b>EMISIÓN:</b> NORMAL<br/>
        <b>CLAVE DE ACCESO:</b><br/>
        <font size="6.5">{clave_acceso}</font>
        """

        header_table = Table(
            [[Paragraph(comp_text, box_text), Paragraph(inv_box_text, box_text)]],
            colWidths=[4.0 * inch, 3.2 * inch]
        )
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (1, 0), (1, 0), 1, colors.HexColor('#cbd5e1')),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#f8fafc')),
            ('PADDING', (1, 0), (1, 0), 8),
        ]))

        elements.append(header_table)
        elements.append(Spacer(1, 10))

        # --- CLIENT INFO BOX ---
        client_name = invoice_data.get("client_nombre", "CONSUMIDOR FINAL")
        client_ident = invoice_data.get("client_identificacion", "9999999999999")
        client_dir = invoice_data.get("client_direccion", "Ciudad")
        client_email = invoice_data.get("client_email", "")
        forma_pago = invoice_data.get("forma_pago", "EFECTIVO")

        client_text = f"""
        <b>Razón Social / Nombres:</b> {client_name}<br/>
        <b>Identificación (RUC/Cédula):</b> {client_ident}<br/>
        <b>Dirección:</b> {client_dir} &nbsp;&nbsp;&nbsp;&nbsp; <b>Email:</b> {client_email}<br/>
        <b>Fecha Emisión:</b> {invoice_data.get('fecha_emision')} &nbsp;&nbsp;&nbsp;&nbsp; <b>Forma de Pago:</b> {forma_pago}
        """

        client_table = Table(
            [[Paragraph("<b>DATOS DEL COMPRADOR / CLIENTE</b>", box_title)],
             [Paragraph(client_text, box_text)]],
            colWidths=[7.2 * inch]
        )
        client_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(client_table)
        elements.append(Spacer(1, 12))

        # --- ITEMS TABLE ---
        table_data = [[
            Paragraph("Cod. Principal", table_header),
            Paragraph("Cant", table_header),
            Paragraph("Descripción", table_header),
            Paragraph("P. Unitario", table_header),
            Paragraph("Desc.", table_header),
            Paragraph("Precio Total", table_header)
        ]]

        for item in items:
            table_data.append([
                Paragraph(item.get("codigo", ""), table_cell),
                Paragraph(f"{item.get('cantidad', 1):.2f}", table_cell_num),
                Paragraph(item.get("descripcion", ""), table_cell),
                Paragraph(f"${item.get('precio_unitario', 0.0):.2f}", table_cell_num),
                Paragraph(f"${item.get('descuento', 0.0):.2f}", table_cell_num),
                Paragraph(f"${item.get('subtotal', 0.0):.2f}", table_cell_num)
            ])

        items_table = Table(
            table_data,
            colWidths=[1.1 * inch, 0.6 * inch, 3.1 * inch, 0.8 * inch, 0.7 * inch, 0.9 * inch]
        )
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
        ]))

        elements.append(items_table)
        elements.append(Spacer(1, 10))

        # --- TOTALS AND QR CODE SECTION ---
        # Generate QR Code buffer
        qr_img_element = None
        try:
            qr = qrcode.QRCode(version=1, box_size=3, border=2)
            qr.add_data(clave_acceso)
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="black", back_color="white")
            
            img_buffer = io.BytesIO()
            img_qr.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            qr_img_element = Image(img_buffer, width=1.3 * inch, height=1.3 * inch)
        except Exception:
            qr_img_element = Paragraph("<b>SRI ECUADOR</b><br/>Firma Electrónica", box_text)

        # Generate Code128 barcode with clave_acceso
        barcode_element = None
        try:
            barcode = code128.Code128(
                clave_acceso,
                barWidth=0.018 * inch,
                barHeight=0.45 * inch,
                humanReadable=False,
            )
            barcode_width = barcode.width
            barcode_height = barcode.height
            drawing = Drawing(barcode_width, barcode_height)
            drawing.add(barcode)
            barcode_buf = io.BytesIO()
            renderPDF.draw(drawing, barcode_buf, 0, 0)
            # Render as PNG via reportlab built-in
            from reportlab.graphics import renderPM
            barcode_png_buf = io.BytesIO()
            renderPM.drawToFile(drawing, barcode_png_buf, fmt='PNG')
            barcode_png_buf.seek(0)
            # Scale to fit page width
            max_w = 7.2 * inch
            scale = min(1.0, max_w / barcode_width)
            barcode_element = Image(
                barcode_png_buf,
                width=barcode_width * scale,
                height=barcode_height * scale
            )
        except Exception:
            barcode_element = Paragraph(
                f"<font size=6><b>Clave de Acceso:</b> {clave_acceso}</font>",
                box_text
            )

        barcode_label = ParagraphStyle(
            'BarcodeLabel',
            parent=styles['Normal'],
            fontSize=6,
            leading=8,
            textColor=colors.HexColor('#64748b'),
            alignment=1
        )

        info_adicional_text = f"""
        <b>INFORMACIÓN ADICIONAL</b><br/>
        <b>Email Cliente:</b> {client_email}<br/>
        <b>Teléfono:</b> {company_info.get('telefono', '')}<br/>
        <b>Generado por:</b> Sistema POS Fleting<br/>
        <b>Estado SRI:</b> COMPROBANTE AUTORIZADO
        """

        left_cell_content = [
            Paragraph(info_adicional_text, box_text),
            Spacer(1, 5),
            qr_img_element
        ]

        # Totals Table
        tot_15 = invoice_data.get("subtotal_15", 0.0)
        tot_0 = invoice_data.get("subtotal_0", 0.0)
        tot_sin_imp = invoice_data.get("subtotal_sin_impuestos", 0.0)
        tot_desc = invoice_data.get("total_descuento", 0.0)
        iva_val = invoice_data.get("iva_total", 0.0)
        imp_total = invoice_data.get("importe_total", 0.0)

        totals_data = [
            [Paragraph("<b>SUBTOTAL 15%</b>", box_text), Paragraph(f"${tot_15:.2f}", table_cell_num)],
            [Paragraph("<b>SUBTOTAL 0%</b>", box_text), Paragraph(f"${tot_0:.2f}", table_cell_num)],
            [Paragraph("<b>SUBTOTAL SIN IMPUESTOS</b>", box_text), Paragraph(f"${tot_sin_imp:.2f}", table_cell_num)],
            [Paragraph("<b>TOTAL DESCUENTO</b>", box_text), Paragraph(f"${tot_desc:.2f}", table_cell_num)],
            [Paragraph("<b>IVA 15%</b>", box_text), Paragraph(f"${iva_val:.2f}", table_cell_num)],
            [Paragraph("<b><font size=9 color='#2563eb'>VALOR TOTAL</font></b>", box_text), Paragraph(f"<b><font size=10 color='#2563eb'>${imp_total:.2f}</font></b>", table_cell_num)]
        ]

        totals_table = Table(totals_data, colWidths=[2.1 * inch, 1.1 * inch])
        totals_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#eff6ff')),
            ('PADDING', (0, 0), (-1, -1), 4)
        ]))

        footer_table = Table(
            [[left_cell_content, totals_table]],
            colWidths=[4.0 * inch, 3.2 * inch]
        )
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        elements.append(footer_table)
        elements.append(Spacer(1, 10))

        # --- BARCODE SECTION ---
        barcode_table = Table(
            [[barcode_element]],
            colWidths=[7.2 * inch]
        )
        barcode_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(barcode_table)
        elements.append(Paragraph(
            "<font size=6 color='#64748b'><b>CLAVE DE ACCESO SRI:</b> " + clave_acceso + "</font>",
            ParagraphStyle('CA', parent=styles['Normal'], alignment=1, fontSize=6, leading=8)
        ))

        doc.build(elements)
        return str(pdf_file)
