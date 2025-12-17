from http import HTTPStatus

import jwt
import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import User
from app.security import SECRET_KEY, create_access_token, get_password_hash

from .database import SessionLocalTest


@pytest.fixture
def session():
    db = SessionLocalTest()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(session):

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def user(session):
    raw_password = "123"
    user = User(
        username="Admin",
        email="admin@test.com",
        password=get_password_hash(raw_password)
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return user, raw_password


def test_jwt():
    data = {"test": "test"}
    token = create_access_token(data)

    decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

    assert decoded["test"] == data["test"]
    assert "exp" in decoded


def test_get_token(client, user):
    user_obj, raw_password = user
    response = client.post(
        '/token',
        data={'username': user_obj.username, 'password': raw_password},
    )
    token = response.json()

    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in token
    assert 'token_type' in token
