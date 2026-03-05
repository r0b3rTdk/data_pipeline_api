"""
Readiness endpoint tests.

Covers:
- Successful readiness response (200) with API/DB checks
- Request ID propagation via X-Request-Id header
- Process time header presence (X-Process-Time-Ms)
- Database failure path returning 503 via get_db override
"""

from sqlalchemy import text

from app.infra.db.session import get_db
from app.main import app


def test_ready_ok_returns_200_and_checks(client):
    r = client.get("/api/v1/ready")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok"
    assert body["checks"]["api"] == "ok"
    assert body["checks"]["db"] == "ok"
    assert isinstance(body["request_id"], str) and len(body["request_id"]) > 0


def test_ready_propagates_request_id_header(client):
    custom = "my-custom-request-id-123"
    r = client.get("/api/v1/ready", headers={"X-Request-Id": custom})
    assert r.status_code == 200, r.text
    assert r.headers.get("X-Request-Id") == custom
    assert r.json().get("request_id") == custom


def test_ready_sets_process_time_header(client):
    r = client.get("/api/v1/ready")
    assert r.status_code == 200, r.text
    assert "X-Process-Time-Ms" in r.headers
    assert r.headers["X-Process-Time-Ms"].isdigit()


def test_ready_db_fail_returns_503(monkeypatch, client):
    """
    Simula falha no DB sobrescrevendo get_db para retornar um objeto com execute() quebrando.
    """
    class DummyDBFail:
        def execute(self, *_args, **_kwargs):
            raise Exception("db down")

    def _override_get_db():
        yield DummyDBFail()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        r = client.get("/api/v1/ready")
        assert r.status_code == 503, r.text
        body = r.json()
        assert body["status"] == "fail"
        assert body["checks"]["api"] == "ok"
        assert body["checks"]["db"] == "fail"
        assert isinstance(body["request_id"], str) and len(body["request_id"]) > 0
    finally:
        app.dependency_overrides.clear()