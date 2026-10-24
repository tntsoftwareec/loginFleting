"""Utilidades compartidas para la generación de PDF con reportlab
(usadas por la exportación de listados).
"""
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

# Paleta
INK = colors.HexColor("#0f172a")
SLATE = colors.HexColor("#334155")
MUTED = colors.HexColor("#64748b")
LINE = colors.HexColor("#cbd5e1")
BAND = colors.HexColor("#1e293b")
SOFT = colors.HexColor("#f1f5f9")
ACCENT = colors.HexColor("#1d4ed8")


def build_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=16, textColor=INK, leading=19,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=9, textColor=SLATE, leading=12,
        ),
        "label": ParagraphStyle(
            "label", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=7, textColor=MUTED, leading=9,
        ),
        "value": ParagraphStyle(
            "value", parent=base["Normal"], fontName="Helvetica",
            fontSize=8.5, textColor=INK, leading=11,
        ),
        "small": ParagraphStyle(
            "small", parent=base["Normal"], fontName="Helvetica",
            fontSize=7.5, textColor=SLATE, leading=10,
        ),
        "cell": ParagraphStyle(
            "cell", parent=base["Normal"], fontName="Helvetica",
            fontSize=8, textColor=INK, leading=10,
        ),
        "cell_b": ParagraphStyle(
            "cell_b", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=8, textColor=INK, leading=10,
        ),
        "cell_r": ParagraphStyle(
            "cell_r", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=8, textColor=INK, leading=10, alignment=TA_RIGHT,
        ),
        "head": ParagraphStyle(
            "head", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=8, textColor=colors.white, leading=10, alignment=TA_CENTER,
        ),
        "total": ParagraphStyle(
            "total", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=11, textColor=INK, leading=13, alignment=TA_RIGHT,
        ),
        "note": ParagraphStyle(
            "note", parent=base["Normal"], fontName="Helvetica-Oblique",
            fontSize=7, textColor=MUTED, leading=9,
        ),
    }


def money(value) -> str:
    try:
        return f"{float(value or 0):,.2f}"
    except (TypeError, ValueError):
        return "0.00"
