from .exporter_interface import AuditLogExporter
import csv
import io


class CSVExporter(AuditLogExporter):
    def export(self, logs: list[dict]) -> bytes:
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
