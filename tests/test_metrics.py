"""
Metrics tests.

Ensures metrics endpoint returns expected fields.
"""
from tests.conftest import ensure_user, login


def test_metrics_returns_fields(client, db_session):
    ensure_user(db_session, "admin_metrics", "Admin@123", "admin")
    token = login(client, "admin_metrics", "Admin@123")

    r = client.get("/api/v1/metrics", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    data = r.json()

    for k in ["total_raw", "total_trusted", "total_rejected", "rejection_rate", "duplicates", "top_rejection_categories"]:
        assert k in data