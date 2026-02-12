"""
Audit tests.

Ensures that modifying a trusted event creates an audit log entry.
"""
from sqlalchemy import func

from tests.conftest import ensure_user, login

from app.infra.db.models.audit_log import AuditLog
from app.infra.db.models.trusted_event import TrustedEvent


def test_patch_trusted_creates_audit(client, db_session):
    # Cria usuário admin
    admin = ensure_user(db_session, "admin_audit", "Admin@123", "admin")
    token = login(client, "admin_audit", "Admin@123")

    # precisa existir um TrustedEvent para patch
    t = db_session.query(TrustedEvent).order_by(TrustedEvent.id.desc()).first()
    if not t:
        raise AssertionError(
            "No trusted_event found. Create one via ingest before running tests, or adapt fixture to insert a TrustedEvent."
        )

    # Conta logs antes
    before_count = db_session.query(func.count(AuditLog.id)).scalar() or 0

    # Executa PATCH
    r = client.patch(
        f"/api/v1/trusted/{t.id}",
        json={"reason": "teste", "event_status": "APPROVED"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text

    # Verifica se audit_log foi criado
    after_count = db_session.query(func.count(AuditLog.id)).scalar() or 0
    assert after_count == before_count + 1