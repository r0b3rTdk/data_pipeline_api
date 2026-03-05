"""
Metrics tests.

Ensures metrics endpoint returns expected fields.
"""
from tests.conftest import ensure_user, login


def test_metrics_includes_http_and_routes(client, db_session):
    from tests.conftest import ensure_user, login

    ensure_user(db_session, "admin_metrics_obs", "Admin@123", "admin")
    token = login(client, "admin_metrics_obs", "Admin@123")

    r = client.get("/api/v1/metrics", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    data = r.json()

    assert "http" in data
    http = data["http"]
    for k in ["uptime_seconds", "requests_total", "errors_4xx_total", "errors_5xx_total"]:
        assert k in http

    assert "http_routes" in data
    assert isinstance(data["http_routes"], dict)