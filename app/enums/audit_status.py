from enum import Enum


class AuditStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    DENIED = "DENIED"
    PARTIAL = "PARTIAL"
    VALIDATION_ERROR = "VALIDATION_ERROR"
