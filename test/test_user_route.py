from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_header():
    token = create_access_token({"sub": "Admin"})
    return {"Authorization": f"Bearer {token}"}


def test_read_users(client, auth_header):
    response = client.get('/users/', headers=auth_header)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'users': [
            {
                'created_at': '2025-11-17T11:53:10',
                'email': 'admin@test.com',
                'enabled': True,
                'id': 'e19cb553-74bc-4c83-b198-a4c99650e292',
                'userRole': 3,
                'username': 'test-user',
            },
            {
                'created_at': '2025-11-24T13:03:09',
                'email': 'diogo.xavier@cladtek.com',
                'enabled': True,
                'id': '3385c3a3-07dc-4e6a-9a7e-39207cca345a',
                'userRole': 3,
                'username': 'Diogo',
            },
            {
                'created_at': '2025-11-24T13:03:36',
                'email': 'admin@cladtek.com',
                'enabled': True,
                'id': 'a1a187ef-b5df-4725-8a74-d20ae9d5776d',
                'userRole': 1,
                'username': 'Admin',
            },
            {
                'created_at': '2025-11-27T14:42:13',
                'email': 'user@example.com',
                'enabled': True,
                'id': '2a677fcb-9b1b-4265-a0ef-760c717aa779',
                'userRole': 3,
                'username': 'string',
            }
        ]
    }
