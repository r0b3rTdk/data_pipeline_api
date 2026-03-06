"""
Authentication tests.

Covers:
- Successful login returns access/refresh tokens
- Invalid credentials return 401
- Brute-force protection blocks after repeated failures (429)
- Refresh token exchange returns a new access token
- Login rate limiting returns 429 when limit is exceeded
"""

from tests.conftest import ensure_user
from app.core.settings import settings


def test_login_ok_returns_access_and_refresh(client, db_session):
    # Cria usuário válido para autenticação
    ensure_user(db_session, "admin_test", "Admin@123", "admin")

    # Login deve retornar tokens JWT (access + refresh)
    r = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_test", "password": "Admin@123"},
        headers={"X-Client-IP": "1.1.1.1"},  # IP fixo para testes / rate-limit
    )
    assert r.status_code == 200, r.text
    body = r.json()

    assert isinstance(body["access_token"], str) and len(body["access_token"]) > 20
    assert isinstance(body["refresh_token"], str) and len(body["refresh_token"]) > 20
    assert body["token_type"] == "bearer"


def test_login_fail_still_401(client, db_session):
    # Usuário existe, mas senha é inválida
    ensure_user(db_session, "admin_test2", "Admin@123", "admin")

    r = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_test2", "password": "WRONG"},
        headers={"X-Client-IP": "2.2.2.2"},
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "invalid_credentials"


def test_bruteforce_blocks_after_5_failures(client, db_session):
    # Garante usuário válido, mas vamos errar a senha para acumular falhas
    ensure_user(db_session, "bf_user", "Admin@123", "admin")

    ip = "3.3.3.3"
    for _ in range(5):
        # Falhas repetidas devem acumular tentativas (401) e eventualmente bloquear (429)
        r = client.post(
            "/api/v1/auth/login",
            json={"username": "bf_user", "password": "WRONG"},
            headers={"X-Client-IP": ip},
        )
        assert r.status_code in (401, 429)

    # Após atingir o limite, deve estar bloqueado
    r = client.post(
        "/api/v1/auth/login",
        json={"username": "bf_user", "password": "WRONG"},
        headers={"X-Client-IP": ip},
    )
    assert r.status_code == 429
    assert r.json()["detail"] == "too_many_login_attempts"


def test_refresh_flow(client, db_session):
    # Login e troca do refresh token por um novo access token
    ensure_user(db_session, "ref_user", "Admin@123", "admin")

    ip = "4.4.4.4"
    r = client.post(
        "/api/v1/auth/login",
        json={"username": "ref_user", "password": "Admin@123"},
        headers={"X-Client-IP": ip},
    )
    assert r.status_code == 200, r.text
    refresh = r.json()["refresh_token"]

    r2 = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh},
        headers={"X-Client-IP": ip},
    )
    assert r2.status_code == 200, r2.text
    assert isinstance(r2.json()["access_token"], str) and len(r2.json()["access_token"]) > 20


def test_rate_limit_login_429(client, db_session):
    
    settings.LOGIN_RATE_LIMIT = "5/minute"
    # Estoura o rate-limit do endpoint de login (ex: 5/min → 6ª request retorna 429)
    ensure_user(db_session, "rl_user", "Admin@123", "admin")

    ip = "5.5.5.5"
    for i in range(5):
        r = client.post(
            "/api/v1/auth/login",
            json={"username": "rl_user", "password": "Admin@123"},
            headers={"X-Client-IP": ip},
        )
        assert r.status_code == 200, (i, r.text)

    # Requisição extra deve ser bloqueada pelo rate limit
    r = client.post(
        "/api/v1/auth/login",
        json={"username": "rl_user", "password": "Admin@123"},
        headers={"X-Client-IP": ip},
    )
    assert r.status_code == 429