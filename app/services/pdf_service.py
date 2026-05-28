from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def build_derivative_pdf(expression: str, steps: list[str], derivative: str) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Calculus Visual — Derivative Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"f(x) = {expression}", styles["Heading2"]),
        Spacer(1, 8),
    ]
    for i, step in enumerate(steps, 1):
        story.append(Paragraph(f"Step {i}: {step}", styles["Normal"]))
        story.append(Spacer(1, 6))
    story.append(Paragraph(f"Result: f'(x) = {derivative}", styles["Heading2"]))
    doc.build(story)
    return buffer.getvalue()
