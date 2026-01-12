import csv
import io

from .exporter_interface import AuditLogExporter


class CSVExporter(AuditLogExporter):
    def export(self, logs: list[dict]) -> bytes:  # noqa: PLR6301
        if not logs:
            return b""

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=logs[0].keys(),
        )

        writer.writeheader()
        writer.writerows(logs)

        return output.getvalue().encode("utf-8")
