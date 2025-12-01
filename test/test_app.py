from http import HTTPStatus

from fastapi.testclient import TestClient

from app import main

def test_root_must_return_ok():
    client = TestClient(main.app)
    
    response = client.get('/')  

    assert response.status_code == HTTPStatus.OK  
    assert response.json() == {"status":"online","version":"v1.0.0","docs":"/docs"}