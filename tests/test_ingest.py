"""
Ingestion tests.

Ensures ingest endpoint requires API key.
"""
from tests.conftest import ensure_user, login


def test_ingest_still_works_requires_api_key(client, db_session):

    # Sem X-API-Key deve falhar
    r = client.post("/api/v1/ingest", json={
        "source": "partner_a",
        "external_id": "t-ing-1",
        "entity_id": "ent-1",
        "event_status": "NEW",
        "event_timestamp": "2026-02-10T00:00:00Z",
        "event_type": "ORDER",
        "severity": "low",
        "payload": {"a": 1},
    })
    assert r.status_code in (401, 422), r.text