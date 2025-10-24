from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Mapped, registry, mapped_column

table_registry = registry()

@table_registry.mapped_as_dataclass
class User:
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    enabled: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
