def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Healthy"
    assert data["application"] == "A4A Learn"
    assert data["version"] == "1.0.0"