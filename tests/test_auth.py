"""
Authentication tests.

Validates login success and failure scenarios.
"""
from tests.conftest import ensure_user, login


def test_login_ok(client, db_session):
    # Cria usuário válido
    ensure_user(db_session, "admin_test", "Admin@123", "admin")
    
    # Login deve retornar token JWT
    token = login(client, "admin_test", "Admin@123")
    
    assert isinstance(token, str)
    assert len(token) > 20


def test_login_fail(client, db_session):
    # Usuário existe
    ensure_user(db_session, "admin_test2", "Admin@123", "admin")

    # Senha errada deve retornar 401
    r = client.post(
        "/api/v1/auth/login", 
        json={"username": "admin_test2", "password": "WRONG"}
    )
    
    assert r.status_code == 401
    assert r.json()["detail"] == "invalid_credentials"