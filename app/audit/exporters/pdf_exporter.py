import io
from reportlab.platypus import (  # type: ignore
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from typing import Iterable, Any
from reportlab.lib.styles import getSampleStyleSheet  # type: ignore
from reportlab.lib.pagesizes import landscape, A4  # type: ignore
from reportlab.lib import colors  # type: ignore
from .exporter_interface import AuditLogExporter


class PDFExporter(AuditLogExporter):
    def export(self, logs: Iterable[dict[str, Any]]) -> bytes:  # noqa: PLR6301
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        elements = []

        styles = getSampleStyleSheet()

        elements.append(Paragraph("Audit Logs Report", styles["Title"]))
        elements.append(Spacer(1, 12))

        log_list = list(logs)

        if log_list:
            headers = list(log_list[0].keys())
            table_data = [
                [Paragraph(f"<b>{h}</b>", styles["Normal"]) for h in headers]
                ]

            for log in logs:
                row = []
                for val in log.values():
                    text = str(val) if val is not None else ""
                    row.append(Paragraph(text, styles["Normal"]))
                table_data.append(row)

            table = Table(table_data, repeatRows=1)

            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#555555")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ]))

            elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return buffer.read()
