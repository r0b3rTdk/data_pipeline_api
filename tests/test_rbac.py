"""
RBAC tests.

Ensures role-based access control is enforced.
"""
from tests.conftest import ensure_user, login


def test_rbac_forbidden_operator_on_rejections(client, db_session):
    ensure_user(db_session, "op_test", "Op@123", "operator")
    token = login(client, "op_test", "Op@123")

    r = client.get("/api/v1/rejections?page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["detail"] == "forbidden"