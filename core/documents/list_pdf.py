"""Exportación de listados (clientes, productos, facturas, cotizaciones) a PDF."""
import os
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.documents.pdf_common import BAND, LINE, SOFT, build_styles

FOOTER_TEXT = "Sistema ERP · Reporte generado automáticamente"


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(14 * mm, 8 * mm, FOOTER_TEXT)
    canvas.drawRightString(doc.pagesize[0] - 14 * mm, 8 * mm, f"Página {doc.page}")
    canvas.restoreState()


def export_list_pdf(path_or_buffer, title: str, headers, rows, subtitle: str = "",
                    landscape_mode: bool = True):
    pagesize = landscape(A4) if landscape_mode else A4
    doc = SimpleDocTemplate(
        path_or_buffer,
        pagesize=pagesize,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=16 * mm,
        title=title,
    )
    styles = build_styles()

    story = [Paragraph(title, styles["title"])]
    if subtitle:
        story.append(Spacer(1, 3))
        story.append(Paragraph(subtitle, styles["small"]))
    story.append(Spacer(1, 10))

    data = [[Paragraph(str(h), styles["head"]) for h in headers]]
    for row in rows:
        if isinstance(row, dict):
            data.append([
                Paragraph("" if row.get(h) is None else str(row.get(h)), styles["cell"])
                for h in headers
            ])
        else:
            data.append([
                Paragraph("" if value is None else str(value), styles["cell"])
                for value in row
            ])

    if not rows:
        data.append([Paragraph("Sin registros.", styles["cell"])] + [Paragraph("", styles["cell"])] * (len(headers) - 1))

    usable = pagesize[0] - 24 * mm
    col_width = usable / max(len(headers), 1)
    table = Table(data, colWidths=[col_width] * len(headers), repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BAND),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT]),
    ]))
    story.append(table)

    if isinstance(path_or_buffer, (str, os.PathLike)):
        os.makedirs(os.path.dirname(os.path.abspath(path_or_buffer)), exist_ok=True)
        doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
        return str(path_or_buffer)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return path_or_buffer


def list_pdf_bytes(title: str, headers, rows, subtitle: str = "") -> bytes:
    buffer = BytesIO()
    export_list_pdf(buffer, title, headers, rows, subtitle=subtitle)
    return buffer.getvalue()
