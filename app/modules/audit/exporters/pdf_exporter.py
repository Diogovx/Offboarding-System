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
from .base import AuditLogExporter
from .base import ACTION_LABELS, COLUMN_HEADERS, STATUS_LABELS


class PDFExporter(AuditLogExporter):
    def export(self, logs: Iterable[dict[str, Any]]) -> bytes:  # noqa: PLR6301
        display_columns = [
            "created_at",
            "username",
            "action",
            "target_username",
            "status",
            "ip_address"
        ]

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
            headers = [COLUMN_HEADERS.get(col, col) for col in display_columns]
            table_data = [
                [Paragraph(
                    f"<font color='white'><b>{h}</b></font>", styles["Normal"]
                ) for h in headers]
            ]

            for log in logs:
                row = []
                row.append(
                    Paragraph(str(log.get("created_at")), styles["Normal"])
                )
                row.append(
                    Paragraph(str(log.get("username")), styles["Normal"])
                )
                row.append(
                    Paragraph(ACTION_LABELS.get(
                        log.get("action"), log.get("action")), styles["Normal"]
                    )
                )
                row.append(
                    Paragraph(str(
                        log.get("target_username") or "—"), styles["Normal"]
                    )
                )
                row.append(
                    Paragraph(STATUS_LABELS.get(
                        log.get("status"), log.get("status")), styles["Normal"]
                    )
                )
                row.append(
                    Paragraph(str(log.get("ip_address")), styles["Normal"])
                )
                table_data.append(row)

            table = Table(table_data, repeatRows=1)

            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#555555")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))

            elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return buffer.read()
