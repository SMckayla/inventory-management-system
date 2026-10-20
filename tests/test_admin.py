from tests.test_external_api import NUTELLA, FakeResponse


def test_dashboard_renders_lookup_and_empty_inventory(client):
    response = client.get("/")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Inventory Admin" in page
    assert "Open Food Facts" in page
    assert "No inventory items yet." in page
    assert 'name="barcode"' in page


def test_admin_can_create_an_item(client):
    created = client.post(
        "/items",
        data={
            "name": "Rice",
            "quantity": "4",
            "price": "3.00",
            "barcode": "777",
            "category": "Grains",
            "brand": "Lundberg",
            "description": "Brown rice",
        },
        follow_redirects=True,
    )
    page = created.get_data(as_text=True)
    assert "Added Rice." in page
    assert "Rice" in page
    assert "Edit" not in page
    assert "Delete" not in page
    stored = client.get("/api/inventory/1").get_json()
    assert stored["name"] == "Rice"
    assert stored["quantity"] == 4
    assert stored["price"] == 3.0


def test_admin_shows_external_results_without_saving_them(client, store, monkeypatch):
    monkeypatch.setattr(
        "app.openfoodfacts.requests.get",
        lambda *args, **kwargs: FakeResponse(NUTELLA),
    )
    lookup = client.get("/", query_string={"barcode": "3017620422003"})
    page = lookup.get_data(as_text=True)
    assert "Nutella" in page
    assert "Ferrero" in page
    assert "Open Food Facts results" in page
    assert store.records == []


def test_admin_reports_a_failed_lookup(client, monkeypatch):
    monkeypatch.setattr(
        "app.openfoodfacts.requests.get",
        lambda *args, **kwargs: FakeResponse({"status": 0}),
    )
    response = client.get("/", query_string={"barcode": "000"})
    assert "No matching products on Open Food Facts." in response.get_data(as_text=True)


def test_admin_rejects_an_incomplete_item(client):
    response = client.post(
        "/items",
        data={"name": " ", "quantity": "1", "price": "1"},
        follow_redirects=True,
    )
    assert "name is required." in response.get_data(as_text=True)
    assert client.get("/api/inventory").get_json() == []
