def test_request_id_headers_are_present(client):
    """
    Fase 6: middleware deve sempre devolver:
    - X-Request-Id
    - X-Process-Time-Ms
    """
    r = client.get("/api/v1/health")
    assert r.status_code == 200

    assert "X-Request-Id" in r.headers
    assert "X-Process-Time-Ms" in r.headers

    rid = r.headers["X-Request-Id"]
    assert isinstance(rid, str) and len(rid) > 0

    # process time é string numérica
    ms = r.headers["X-Process-Time-Ms"]
    assert ms.isdigit()