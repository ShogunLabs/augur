from fastapi import HTTPException

import app.api.routes.ipos as ipos_route


def test_list_ipos_returns_200_and_allows_missing_optional_fields(
    client,
    monkeypatch,
):
    items = [
        {
            "id": "zepto-ipo",
            "name": "Zepto",
            "status": "upcoming",
            "issue_type": "regular",
            "industry": "e-Commerce",
        },
        {
            "id": "shree-tnb-polymers-limited-ipo",
            "symbol": "SHREETNB",
            "name": "Shree TNB Polymers IPO",
            "status": "open",
            "issue_type": "sme",
            "isin": "INE935K01018",
            "issue_size": 31,
            "industry": "Plastic Products",
            "minimum_price": 47,
            "maximum_price": 52,
            "bidding_start_date": "2026-09-25",
            "bidding_end_date": "2026-09-29",
        },
    ]

    pagination = {
        "page": 1,
        "limit": 10,
        "total": 2,
        "pages": 1,
    }

    def fake_list_ipos(*args, **kwargs):
        return items, pagination

    monkeypatch.setattr(ipos_route, "list_ipos", fake_list_ipos)

    response = client.get("/api/v1/ipos?limit=10")

    assert response.status_code == 200

    body = response.json()

    assert body["pagination"] == pagination
    assert len(body["data"]) == 2

    first = body["data"][0]

    assert first["id"] == "zepto-ipo"
    assert first["name"] == "Zepto"

    assert "symbol" not in first
    assert "isin" not in first
    assert "issue_size" not in first
    assert "minimum_price" not in first
    assert "bidding_start_date" not in first


def test_list_ipos_accepts_filters_pagination_and_sort(
    client,
    monkeypatch,
):
    items = []

    pagination = {
        "page": 2,
        "limit": 5,
        "total": 0,
        "pages": 0,
    }

    captured = {}

    def fake_list_ipos(*args, **kwargs):
        captured.update(kwargs)
        return items, pagination

    monkeypatch.setattr(ipos_route, "list_ipos", fake_list_ipos)

    response = client.get(
        "/api/v1/ipos"
        "?status=open"
        "&issue_type=sme"
        "&page=2"
        "&limit=5"
        "&sort=listing_date"
    )

    assert response.status_code == 200
    assert response.json() == {
        "data": [],
        "pagination": pagination,
    }

    assert captured["status"] == "open"
    assert captured["issue_type"] == "sme"
    assert captured["page"] == 2
    assert captured["limit"] == 5
    assert captured["sort"] == "listing_date"


def test_list_ipos_rejects_invalid_limit(client):
    response = client.get("/api/v1/ipos?limit=0")

    assert response.status_code == 422


def test_get_ipo_returns_detail(client, monkeypatch):
    payload = {
        "id": "autofurnish-limited-ipo",
        "symbol": "AFLTD",
        "name": "Autofurnish IPO",
        "status": "open",
        "issue_type": "sme",
        "isin": "INE18HI01019",
        "issue_size": 15,
        "industry": "Automobile Two & Three Wheelers",
        "minimum_price": 41,
        "maximum_price": 41,
        "bidding_start_date": "2026-05-21",
        "bidding_end_date": "2026-05-25",
        "lot_size": 3000,
        "minimum_quantity": 6000,
        "listing_exchange": "BSE",
        "drhp_url": "https://example.com/drhp.pdf",
        "timeline": {
            "allotment_date": "2026-05-27",
            "listing_date": "2026-05-29",
        },
        "registrar_info": {
            "name": "SKYLINE FINANCIAL SERVICES PRIVATE LIMITED",
            "registrar": "SKYLINE",
        },
    }

    def fake_get_ipo(*args, **kwargs):
        return payload

    monkeypatch.setattr(ipos_route, "get_ipo", fake_get_ipo)

    response = client.get(
        "/api/v1/ipos/autofurnish-limited-ipo"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == "autofurnish-limited-ipo"
    assert body["symbol"] == "AFLTD"
    assert body["timeline"]["listing_date"] == "2026-05-29"
    assert body["registrar_info"]["registrar"] == "SKYLINE"

    assert "rhp_url" not in body


def test_get_ipo_returns_404_for_unknown_ipo(
    client,
    monkeypatch,
):
    def fake_get_ipo(*args, **kwargs):
        return None

    monkeypatch.setattr(ipos_route, "get_ipo", fake_get_ipo)

    response = client.get(
        "/api/v1/ipos/does-not-exist"
    )

    assert response.status_code == 404

    assert response.json() == {
        "error": {
            "code": "IPO_NOT_FOUND",
            "message": "IPO not found",
            "details": None,
        }
    }


def test_list_schema_accepts_completely_partial_upcoming_ipo(
    client,
    monkeypatch,
):
    items = [
        {
            "id": "future-ipo",
            "name": "Future IPO",
            "status": "upcoming",
            "issue_type": "regular",
        }
    ]

    pagination = {
        "page": 1,
        "limit": 1,
        "total": 1,
        "pages": 1,
    }

    def fake_list_ipos(*args, **kwargs):
        return items, pagination

    monkeypatch.setattr(ipos_route, "list_ipos", fake_list_ipos)

    response = client.get(
        "/api/v1/ipos?limit=1"
    )

    assert response.status_code == 200
    assert response.json()["data"][0] == items[0]
    
def test_get_ipo_returns_standard_404_error(
    client,
    monkeypatch,
):
    def fake_get_ipo(*args, **kwargs):
        return None

    import app.api.routes.ipos as ipos_route

    monkeypatch.setattr(
        ipos_route,
        "get_ipo",
        fake_get_ipo,
    )

    response = client.get(
        "/api/v1/ipos/does-not-exist"
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "IPO_NOT_FOUND",
            "message": "IPO not found",
            "details": None,
        }
    }