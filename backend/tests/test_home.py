import app.api.routes.home as home_route


def test_home_returns_sections(client, monkeypatch):
    payload = {
        "upcoming": [],
        "open": [
            {
                "id": "test-open-ipo",
                "name": "Test Open IPO",
                "status": "open",
                "issue_type": "regular",
            }
        ],
        "closed": [],
        "listed": [],
    }

    def fake_get_home(*args, **kwargs):
        return payload

    monkeypatch.setattr(
        home_route,
        "get_home",
        fake_get_home,
    )

    response = client.get("/api/v1/home")

    assert response.status_code == 200

    assert response.json() == payload


def test_home_accepts_limit(client, monkeypatch):
    captured = {}

    def fake_get_home(*args, **kwargs):
        captured.update(kwargs)

        return {
            "upcoming": [],
            "open": [],
            "closed": [],
            "listed": [],
        }

    monkeypatch.setattr(
        home_route,
        "get_home",
        fake_get_home,
    )

    response = client.get("/api/v1/home?limit=5")

    assert response.status_code == 200
    assert captured["limit"] == 5


def test_home_rejects_invalid_limit(client):
    response = client.get("/api/v1/home?limit=0")

    assert response.status_code == 422