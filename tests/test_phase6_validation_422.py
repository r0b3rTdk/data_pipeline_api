def test_422_returns_standard_body_with_request_id(client):
    """
    Fase 6: 422 deve ser padronizado e conter:
    - code = VALIDATION_ERROR
    - detail = "Validation error"
    - errors (lista)
    - request_id
    """
    r = client.post("/api/v1/auth/login", json={"username": "x"})  # faltando password -> 422
    assert r.status_code == 422

    data = r.json()
    assert data["code"] == "VALIDATION_ERROR"
    assert data["detail"] == "Validation error"
    assert "errors" in data
    assert isinstance(data["errors"], list)
    assert "request_id" in data
    assert isinstance(data["request_id"], str) and len(data["request_id"]) > 0