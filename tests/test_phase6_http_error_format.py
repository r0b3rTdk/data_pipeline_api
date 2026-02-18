def test_404_returns_standard_http_error_with_request_id(client):
    """
    Fase 6: HTTP errors (ex: 404) devem ser padronizados e conter:
    - code = HTTP_ERROR
    - detail
    - request_id
    """
    r = client.get("/__does_not_exist__")
    assert r.status_code == 404

    data = r.json()
    assert data["code"] == "HTTP_ERROR"
    assert "detail" in data
    assert "request_id" in data
    assert isinstance(data["request_id"], str) and len(data["request_id"]) > 0