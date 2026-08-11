def test_database_endpoint(client):
    response = client.get("/database")

    assert response.status_code == 200

    data = response.json()

    assert data["database"] == "Connected"