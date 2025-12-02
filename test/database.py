from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import table_registry


TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocalTest = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine_test
)

table_registry.metadata.create_all(bind=engine_test)
