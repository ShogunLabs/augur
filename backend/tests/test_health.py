import os

import pytest


@pytest.mark.integration
def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }


@pytest.mark.integration
def test_ready(client):
    response = client.get("/ready")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ready"
    assert body["database"] == "ok"


def test_invalid_limit_returns_standard_error(client):
    response = client.get("/api/v1/ipos?limit=0")

    assert response.status_code == 422

    body = response.json()

    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Request validation failed"