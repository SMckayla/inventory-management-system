import requests

from app.openfoodfacts import USER_AGENT, fetch_by_barcode, search_by_name
from app.services import import_product


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return self._payload


NUTELLA = {
    "status": 1,
    "product": {
        "code": "3017620422003",
        "product_name": "Nutella",
        "brands": "Ferrero",
        "categories": "Spreads, Breakfasts",
        "generic_name": "Hazelnut cocoa spread",
        "image_front_url": "https://images.example/nutella.jpg",
    },
}


def test_fetch_by_barcode_normalizes_the_product(monkeypatch):
    captured = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        return FakeResponse(NUTELLA)

    monkeypatch.setattr("app.openfoodfacts.requests.get", fake_get)
    product = fetch_by_barcode("3017620422003")
    assert product["name"] == "Nutella"
    assert product["barcode"] == "3017620422003"
    assert product["brand"] == "Ferrero"
    assert product["category"] == "Spreads"
    assert product["description"] == "Hazelnut cocoa spread"
    assert "3017620422003" in captured["url"]
    assert captured["headers"]["User-Agent"] == USER_AGENT


def test_unknown_barcode_and_http_404(monkeypatch):
    monkeypatch.setattr(
        "app.openfoodfacts.requests.get",
        lambda *args, **kwargs: FakeResponse({"status": 0, "product": None}),
    )
    assert fetch_by_barcode("000") is None

    monkeypatch.setattr(
        "app.openfoodfacts.requests.get",
        lambda *args, **kwargs: FakeResponse({}, status_code=404),
    )
    assert fetch_by_barcode("000") is None


def test_search_by_name(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        assert "search.pl" in url
        assert params["search_terms"] == "oat milk"
        return FakeResponse(
            {"products": [{"code": "999", "product_name": "Oat Milk", "brands": "Oatly"}]}
        )

    monkeypatch.setattr("app.openfoodfacts.requests.get", fake_get)
    products = search_by_name("oat milk")
    assert products[0]["name"] == "Oat Milk"
    assert products[0]["barcode"] == "999"


def test_lookup_route_by_barcode_and_name(client, monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        if params:
            return FakeResponse({"products": [{"code": "999", "product_name": "Oat Milk"}]})
        return FakeResponse(NUTELLA)

    monkeypatch.setattr("app.openfoodfacts.requests.get", fake_get)

    by_barcode = client.get("/api/external/products", query_string={"barcode": "3017620422003"})
    assert by_barcode.status_code == 200
    body = by_barcode.get_json()
    assert body["source"] == "openfoodfacts"
    assert body["products"][0]["name"] == "Nutella"

    by_name = client.get("/api/external/products", query_string={"name": "oat"})
    assert by_name.get_json()["products"][0]["name"] == "Oat Milk"

    missing = client.get("/api/external/products")
    assert missing.status_code == 400


def test_lookup_reports_an_outage(client, monkeypatch):
    def boom(*args, **kwargs):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr("app.openfoodfacts.requests.get", boom)
    response = client.get("/api/external/products", query_string={"barcode": "123"})
    assert response.status_code == 502
    assert "unavailable" in response.get_json()["error"]


def test_import_adds_the_product_to_the_database_array(client, store, monkeypatch):
    monkeypatch.setattr(
        "app.openfoodfacts.requests.get",
        lambda *args, **kwargs: FakeResponse(NUTELLA),
    )
    response = client.post(
        "/api/inventory/import",
        json={"barcode": "3017620422003", "quantity": 6, "price": 4.25},
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["name"] == "Nutella"
    assert body["quantity"] == 6
    assert body["price"] == 4.25
    assert body["brand"] == "Ferrero"
    assert len(store.records) == 1
    assert store.records[0]["barcode"] == "3017620422003"
    assert client.get("/api/inventory").get_json()[0]["name"] == "Nutella"


def test_import_by_name_uses_match_index(store, monkeypatch):
    payload = {
        "products": [
            {"code": "1", "product_name": "First Oat"},
            {"code": "2", "product_name": "Second Oat"},
        ]
    }
    monkeypatch.setattr(
        "app.openfoodfacts.requests.get",
        lambda *args, **kwargs: FakeResponse(payload),
    )
    item, error = import_product(store, name="oat", quantity=3, price=2, match_index=1)
    assert error is None
    assert item["name"] == "Second Oat"
    assert store.records[0]["barcode"] == "2"

    missing, error = import_product(store, name="oat", match_index=5)
    assert missing is None
    assert "match_index" in error
    assert len(store.records) == 1


def test_import_validation_and_not_found(client, monkeypatch):
    monkeypatch.setattr(
        "app.openfoodfacts.requests.get",
        lambda *args, **kwargs: FakeResponse({"status": 0}),
    )
    not_found = client.post("/api/inventory/import", json={"barcode": "000", "quantity": 1})
    assert not_found.status_code == 404

    invalid = client.post("/api/inventory/import", json={"barcode": "000", "quantity": -2})
    assert invalid.status_code == 400

    neither = client.post("/api/inventory/import", json={"quantity": 1})
    assert neither.status_code == 400

    not_json = client.post("/api/inventory/import", data="nope", content_type="text/plain")
    assert not_json.status_code == 400
