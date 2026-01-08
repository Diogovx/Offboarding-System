import json
from .exporter_interface import AuditLogExporter
from typing import Iterable

class JSONLExporter(AuditLogExporter):
    def export(self, logs: Iterable[dict]) -> bytes:
        lines = [json.dumps(log, ensure_ascii=False) for log in logs]
        return ("\n".join(lines)).encode("utf-8")
