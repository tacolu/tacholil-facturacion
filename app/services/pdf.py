from __future__ import annotations

import io
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.factura import EstadoFactura, FacturaRead

_ESTADOS_DEFINITIVO = {EstadoFactura.EMITIDA, EstadoFactura.PAGADA, EstadoFactura.CANCELADA}

_LABEL_REGIMEN: dict[str, str] = {
    "iva_general": "IVA General",
    "iva_simplificado": "IVA Simplificado",
    "iva_recargo_equivalencia": "Recargo de Equivalencia",
    "igic_general": "IGIC General",
    "igic_simplificado": "IGIC Simplificado",
    "exento": "Exento",
}

_PAGE_W = 17 * cm


@dataclass
class EmisorPDF:
    nif: str
    razon_social: str
    direccion: str
    nombre_comercial: Optional[str] = None
    codigo_postal: Optional[str] = None
    municipio: Optional[str] = None
    provincia: Optional[str] = None
    regimen_fiscal: str = "iva_general"


@dataclass
class ReceptorPDF:
    nif: str
    razon_social: str
    direccion: str
    codigo_postal: Optional[str] = None
    municipio: Optional[str] = None
    provincia: Optional[str] = None


@dataclass
class FacturaPDFData:
    factura: FacturaRead
    emisor: EmisorPDF
    receptor: Optional[ReceptorPDF] = None


def render_factura_pdf(factura: FacturaPDFData) -> bytes:
    if factura.factura.estado == EstadoFactura.BORRADOR:
        raise ValueError(
            f"La factura '{factura.factura.numero}' esta en estado "
            f"'{factura.factura.estado.value}' y no genera PDF definitivo"
        )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    story: list = []

    _add_header(story, styles, factura)
    story.append(Spacer(1, 0.5 * cm))
    _add_partes(story, styles, factura)
    story.append(Spacer(1, 0.7 * cm))
    _add_lineas(story, styles, factura)
    story.append(Spacer(1, 0.5 * cm))
    _add_iva_breakdown(story, styles, factura)
    story.append(Spacer(1, 0.3 * cm))
    _add_totales(story, styles, factura)

    doc.build(story)
    return buffer.getvalue()


def _add_header(story: list, styles, factura: FacturaPDFData) -> None:
    fact = factura.factura
    title_style = ParagraphStyle(
        "FacturaTitle", parent=styles["Heading1"],
        fontSize=20, textColor=colors.darkblue, spaceAfter=6,
    )
    normal = styles["Normal"]
    story.append(Paragraph("FACTURA", title_style))
    story.append(Paragraph(f"<b>Numero:</b> {fact.numero}", normal))
    story.append(Paragraph(f"<b>Fecha:</b> {fact.fecha.strftime('%d/%m/%Y')}", normal))
    story.append(Paragraph(f"<b>Estado:</b> {fact.estado.value.upper()}", normal))
    story.append(HRFlowable(width=_PAGE_W, thickness=1.5, color=colors.darkblue))


def _fmt_address(obj) -> str:
    lines = [obj.direccion]
    cp_muni = " ".join(part for part in [obj.codigo_postal, obj.municipio] if part)
    if cp_muni:
        if obj.provincia:
            cp_muni += f" ({obj.provincia})"
        lines.append(cp_muni)
    elif obj.provincia:
        lines.append(obj.provincia)
    return "<br/>".join(lines)


def _add_partes(story: list, styles, factura: FacturaPDFData) -> None:
    normal = styles["Normal"]
    header_style = ParagraphStyle(
        "ParteHeader", parent=normal,
        fontName="Helvetica-Bold", fontSize=9,
        textColor=colors.darkblue, spaceAfter=3,
    )
    body_style = ParagraphStyle("ParteBody", parent=normal, fontSize=8)

    emisor = factura.emisor
    nombre_display = emisor.nombre_comercial or emisor.razon_social
    emisor_cell = [
        Paragraph("EMISOR", header_style),
        Paragraph(nombre_display, body_style),
    ]
    if emisor.nombre_comercial:
        emisor_cell.append(Paragraph(f"({emisor.razon_social})", body_style))
    emisor_cell += [
        Paragraph(f"NIF: {emisor.nif}", body_style),
        Paragraph(_fmt_address(emisor), body_style),
        Paragraph(
            f"Regimen: {_LABEL_REGIMEN.get(emisor.regimen_fiscal, emisor.regimen_fiscal)}",
            body_style,
        ),
    ]

    if factura.receptor:
        rec = factura.receptor
        receptor_cell = [
            Paragraph("RECEPTOR", header_style),
            Paragraph(rec.razon_social, body_style),
            Paragraph(f"NIF: {rec.nif}", body_style),
            Paragraph(_fmt_address(rec), body_style),
        ]
    else:
        receptor_cell = [Paragraph("", normal)]

    half = _PAGE_W / 2
    table = Table([[emisor_cell, receptor_cell]], colWidths=[half, half])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, -1), 8),
        ("RIGHTPADDING", (1, 0), (1, -1), 0),
        ("BOX", (0, 0), (0, -1), 0.5, colors.lightgrey),
        ("BOX", (1, 0), (1, -1), 0.5, colors.lightgrey),
        ("BACKGROUND", (0, 0), (-1, -1), colors.Color(0.97, 0.97, 0.99)),
    ]))
    story.append(table)


def _add_lineas(story: list, styles, factura: FacturaPDFData) -> None:
    normal = styles["Normal"]
    header_style = ParagraphStyle(
        "LineasSectionHeader", parent=normal,
        fontName="Helvetica-Bold", fontSize=9,
        textColor=colors.darkblue, spaceAfter=3,
    )
    story.append(Paragraph("Lineas de factura", header_style))

    col_widths = [6.5 * cm, 1.5 * cm, 2.5 * cm, 1.5 * cm, 2.5 * cm, 2.5 * cm]
    headers = ["Descripcion", "Cantidad", "Precio unit.", "IVA %", "Base imp.", "Cuota IVA"]
    rows: list = [headers]

    for linea in factura.factura.lineas:
        rows.append([
            linea.descripcion,
            str(linea.cantidad),
            f"{linea.precio_unitario:.2f} EUR",
            f"{linea.tipo_iva:.0f}%",
            f"{linea.subtotal:.2f} EUR",
            f"{linea.cuota_iva:.2f} EUR",
        ])

    table = Table(rows, colWidths=col_widths)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for i, _ in enumerate(rows[1:], start=1):
        bg = colors.white if i % 2 == 1 else colors.Color(0.95, 0.95, 0.95)
        style_cmds.append(("BACKGROUND", (0, i), (-1, i), bg))

    table.setStyle(TableStyle(style_cmds))
    story.append(table)


def _add_iva_breakdown(story: list, styles, factura: FacturaPDFData) -> None:
    lineas = factura.factura.lineas
    if not lineas:
        return

    iva_groups: dict[Decimal, dict[str, Decimal]] = defaultdict(
        lambda: {"base": Decimal("0"), "cuota": Decimal("0")}
    )
    for linea in lineas:
        iva_groups[linea.tipo_iva]["base"] += linea.subtotal
        iva_groups[linea.tipo_iva]["cuota"] += linea.cuota_iva

    normal = styles["Normal"]
    header_style = ParagraphStyle(
        "IvaHeader", parent=normal,
        fontName="Helvetica-Bold", fontSize=9,
        textColor=colors.darkblue, spaceAfter=3,
    )
    story.append(Paragraph("Desglose de impuestos", header_style))

    rows: list = [["Tipo IVA", "Base imponible", "Cuota IVA"]]
    for tipo, valores in sorted(iva_groups.items()):
        rows.append([
            f"{tipo:.0f}%",
            f"{valores['base']:.2f} EUR",
            f"{valores['cuota']:.2f} EUR",
        ])

    col_widths = [3.5 * cm, 4 * cm, 4 * cm]
    table = Table(rows, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.steelblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(table)


def _add_totales(story: list, styles, factura: FacturaPDFData) -> None:
    lineas = factura.factura.lineas
    base_total = sum((ln.subtotal for ln in lineas), Decimal("0"))
    iva_total = sum((ln.cuota_iva for ln in lineas), Decimal("0"))
    total = factura.factura.total

    rows = [
        ["Base imponible total:", f"{base_total:.2f} EUR"],
        ["Total IVA:", f"{iva_total:.2f} EUR"],
        ["TOTAL FACTURA:", f"{total:.2f} EUR"],
    ]
    col_widths = [5 * cm, 3.5 * cm]
    table = Table(rows, colWidths=col_widths, hAlign="RIGHT")
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 1), 9),
        ("FONTSIZE", (0, 2), (-1, 2), 11),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("LINEABOVE", (0, 2), (-1, 2), 1.5, colors.darkblue),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
