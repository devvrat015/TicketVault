from app.core.redis_client import redis_client

def test_idempotent_request_returns_stored_result(client):
    key = "test-key-456"

    redis_client.delete(f"idempotency:{key}")

    headers = {
        "Idempotency-Key": key
    }

    # First request
    response_1 = client.post(
        "/test-idempotent",
        headers=headers,
    )

    assert response_1.status_code == 200

    data_1 = response_1.json()

    assert data_1["duplicate"] is False
    assert "result" in data_1

    # Second request with the same idempotency key
    response_2 = client.post(
        "/test-idempotent",
        headers=headers,
    )

    assert response_2.status_code == 200

    data_2 = response_2.json()

    assert data_2["duplicate"] is True
    assert data_2["result"] == data_1["result"]