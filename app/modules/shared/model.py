import uuid
from sqlalchemy import BLOB
from sqlalchemy.types import TypeDecorator


class SqliteUUID(TypeDecorator):
    impl = BLOB
    cache_ok = True

    def process_bind_param(self, value, dialect):  # noqa: PLR6301
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value.bytes
        return uuid.UUID(value).bytes

    def process_result_value(self, value, dialect):  # noqa: PLR6301
        if value is None:
            return None
        return uuid.UUID(bytes=value)
