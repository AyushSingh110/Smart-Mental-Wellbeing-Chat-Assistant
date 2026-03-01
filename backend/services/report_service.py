from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime


class ReportService:

    def __init__(self):
        self.styles = getSampleStyleSheet()

    def generate_pdf(self, user_id: str, summary: str, mhi_avg: float):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        elements.append(
            Paragraph("<b>Smart Mental Well-Being Session Report</b>", self.styles["Title"])
        )
        elements.append(Spacer(1, 0.3 * inch))

        elements.append(
            Paragraph(f"User ID: {user_id}", self.styles["Normal"])
        )
        elements.append(
            Paragraph(f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", self.styles["Normal"])
        )
        elements.append(Spacer(1, 0.3 * inch))

        elements.append(
            Paragraph(f"<b>Average Mental Health Index:</b> {mhi_avg}", self.styles["Normal"])
        )
        elements.append(Spacer(1, 0.3 * inch))

        elements.append(
            Paragraph("<b>Session Summary:</b>", self.styles["Heading2"])
        )
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(
            Paragraph(summary, self.styles["Normal"])
        )

        doc.build(elements)
        buffer.seek(0)

        return buffer