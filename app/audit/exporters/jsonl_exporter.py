import json
from typing import Iterable

from .exporter_interface import AuditLogExporter


class JSONLExporter(AuditLogExporter):
    def export(self, logs: Iterable[dict]) -> bytes:  # noqa: PLR6301
        lines = [json.dumps(log, ensure_ascii=False) for log in logs]
        return ("\n".join(lines)).encode("utf-8")
