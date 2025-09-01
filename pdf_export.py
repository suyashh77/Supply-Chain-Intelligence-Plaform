from __future__ import annotations
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def make_pdf_briefing(title: str, summary_text: str, top_articles: list[dict]) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, title)
    y -= 28

    c.setFont("Helvetica", 11)
    for line in (summary_text or "").split("\n"):
        c.drawString(40, y, line[:110])
        y -= 14
        if y < 80:
            c.showPage(); y = height - 40

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Top Articles:")
    y -= 18

    c.setFont("Helvetica", 10)
    for art in top_articles:
        text = f"- {art.get('title','')} ({art.get('source','')})"
        c.drawString(40, y, text[:110])
        y -= 12
        url = art.get("url")
        if url:
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(50, y, (url or "")[:120])
            c.setFont("Helvetica", 10)
            y -= 14
        if y < 80:
            c.showPage(); y = height - 40

    c.save()
    buffer.seek(0)
    return buffer.read()
