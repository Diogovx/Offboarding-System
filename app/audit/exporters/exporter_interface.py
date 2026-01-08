from abc import ABC, abstractmethod
from collections.abc import Iterable


class AuditLogExporter(ABC):
    @abstractmethod
    def export(self, logs: Iterable[dict]) -> bytes: ...
