import pytest

from .database import SessionLocalTest


@pytest.fixture
def session():
    db = SessionLocalTest()
    try:
        yield db
    finally:
        db.close()
