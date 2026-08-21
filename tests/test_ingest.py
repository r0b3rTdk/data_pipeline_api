"""
Ingestion tests.

Ensures ingest endpoint respects API key validation,
processes valid events, handles deduplication, and rejects conflicts.
"""
import uuid

def test_ingest_unauthorized_invalid_api_key(client, db_session, ingest_source):
    headers = {"X-API-Key": "fake"}
    
    r = client.post("/api/v1/ingest", json={
        "source": "partner_a",
        "external_id": f"t-ing-{uuid.uuid4().hex}",
        "entity_id": "ent-1",
        "event_status": "NEW",
        "event_timestamp": "2026-02-10T00:00:00Z",
        "event_type": "ORDER",
        "severity": "low",
        "payload": {"a": 1},
    }, headers=headers)
    
    assert r.status_code in (401, 403), r.text


def test_ingest_valid_happy_path(client, db_session, ingest_source):
    headers = {"X-API-Key": "partner_a_key_change_me"}
    
    r = client.post("/api/v1/ingest", json={
        "source": "partner_a",
        "external_id": f"happy-{uuid.uuid4().hex}",
        "entity_id": "ent-1",
        "event_status": "NEW",
        "event_timestamp": "2026-02-10T00:00:00Z",
        "event_type": "ORDER",
        "severity": "low",
        "payload": {"a": 1},
    }, headers=headers)
    
    assert r.status_code == 200
    assert r.json()["status"] == "ACCEPTED"


def test_ingest_duplicate_same_hash(client, db_session, ingest_source):
    headers = {"X-API-Key": "partner_a_key_change_me"}
    
    payload_data = {
        "source": "partner_a",
        "external_id": f"dup-{uuid.uuid4().hex}",
        "entity_id": "ent-1",
        "event_status": "NEW",
        "event_timestamp": "2026-02-10T00:00:00Z",
        "event_type": "ORDER",
        "severity": "low",
        "payload": {"a": 1},
    }
    
    r1 = client.post("/api/v1/ingest", json=payload_data, headers=headers)
    assert r1.status_code == 200
    assert r1.json()["status"] == "ACCEPTED"
    
    r2 = client.post("/api/v1/ingest", json=payload_data, headers=headers)
    assert r2.status_code == 200
    assert r2.json()["status"] == "DUPLICATE"


def test_ingest_conflict_different_hash(client, db_session, ingest_source):
    headers = {"X-API-Key": "partner_a_key_change_me"}
    
    payload_data = {
        "source": "partner_a",
        "external_id": f"conflict-{uuid.uuid4().hex}",
        "entity_id": "ent-1",
        "event_status": "NEW",
        "event_timestamp": "2026-02-10T00:00:00Z",
        "event_type": "ORDER",
        "severity": "low",
        "payload": {"a": 1},
    }
    
    r1 = client.post("/api/v1/ingest", json=payload_data, headers=headers)
    assert r1.status_code == 200
    assert r1.json()["status"] == "ACCEPTED"
    
    payload_data["entity_id"] = "ent-999-modificado"
    
    r2 = client.post("/api/v1/ingest", json=payload_data, headers=headers)
    
    assert r2.status_code == 409
    assert r2.json()["detail"]["status"] == "CONFLICT"