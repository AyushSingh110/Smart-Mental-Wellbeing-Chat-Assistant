from __future__ import annotations

from io import BytesIO
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors


_CATEGORY_COLORS = {
    "Stable":           "#48bb78",
    "Mild Stress":      "#68d391",
    "Moderate Distress":"#ed8936",
    "High Risk":        "#fc8181",
    "Depression Risk":  "#e53e3e",
    "Crisis Risk":      "#c53030",
}


class ReportService:

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()

    def _add_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name="SubHeading",
            parent=self.styles["Heading2"],
            fontSize=12,
            spaceAfter=6,
            textColor=colors.HexColor("#1a202c"),
        ))
        self.styles.add(ParagraphStyle(
            name="BodySmall",
            parent=self.styles["Normal"],
            fontSize=9,
            leading=14,
            textColor=colors.HexColor("#4a5568"),
        ))
        self.styles.add(ParagraphStyle(
            name="Disclaimer",
            parent=self.styles["Normal"],
            fontSize=8,
            leading=12,
            textColor=colors.HexColor("#718096"),
        ))

    def generate_pdf(
        self,
        user_id: str,
        summary: str,
        mhi_avg: float,
        session_count: int = 0,
        latest_category: str = "—",
        trend: str = "—",
    ) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=0.8 * inch,
            bottomMargin=0.8 * inch,
            leftMargin=inch,
            rightMargin=inch,
        )
        elements = []
        s = self.styles

        # ── Header ───────────────────────────────────────────────────────────
        elements.append(Paragraph("Smart Mental Well-Being Assistant", s["Title"]))
        elements.append(Paragraph("Session Report", s["SubHeading"]))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
        elements.append(Spacer(1, 0.2 * inch))

        # ── Meta info table ───────────────────────────────────────────────────
        generated_at = datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")
        meta_data = [
            ["Generated", generated_at],
            ["User ID",   str(user_id)],
            ["Sessions",  str(session_count)],
            ["Trend",     trend.capitalize()],
        ]
        meta_table = Table(meta_data, colWidths=[1.5 * inch, 4.5 * inch])
        meta_table.setStyle(TableStyle([
            ("FONTNAME",  (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",  (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#718096")),
            ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#1a202c")),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f7fafc"), colors.white]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 0.3 * inch))

        # ── MHI summary ───────────────────────────────────────────────────────
        elements.append(Paragraph("Mental Health Index Summary", s["SubHeading"]))

        mhi_color = colors.HexColor(_CATEGORY_COLORS.get(latest_category, "#4a5568"))
        mhi_data = [
            ["Average MHI",     f"{mhi_avg:.1f} / 100"],
            ["Last Category",   latest_category],
        ]
        mhi_table = Table(mhi_data, colWidths=[2 * inch, 4 * inch])
        mhi_table.setStyle(TableStyle([
            ("FONTNAME",  (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE",  (0, 0), (-1, -1), 11),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#718096")),
            ("TEXTCOLOR", (1, 0), (1, 0),  colors.HexColor("#2d3748")),
            ("TEXTCOLOR", (1, 1), (1, 1),  mhi_color),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ]))
        elements.append(mhi_table)
        elements.append(Spacer(1, 0.3 * inch))

        # ── AI Summary ────────────────────────────────────────────────────────
        elements.append(Paragraph("Session Analysis", s["SubHeading"]))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
        elements.append(Spacer(1, 0.1 * inch))

        for para in summary.split("\n"):
            if para.strip():
                elements.append(Paragraph(para.strip(), s["BodySmall"]))
                elements.append(Spacer(1, 0.08 * inch))

        elements.append(Spacer(1, 0.4 * inch))

        # ── Disclaimer ────────────────────────────────────────────────────────
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(
            "This report is generated by an AI-based mental well-being assistant and is "
            "intended for personal insight only. It does not constitute a clinical diagnosis "
            "or professional medical advice. If you are experiencing a mental health crisis, "
            "please contact a licensed professional or emergency services immediately.",
            s["Disclaimer"],
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer