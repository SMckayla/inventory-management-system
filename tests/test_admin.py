from tests.test_external_api import NUTELLA, FakeResponse


def test_dashboard_renders_lookup_and_empty_inventory(client):
    response = client.get("/")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Inventory Admin" in page
    assert "Open Food Facts" in page
    assert "No inventory items yet." in page
    assert 'name="barcode"' in page


def test_admin_can_create_update_and_delete(client):
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

    updated = client.post(
        "/items/1/update",
        data={
            "name": "Brown Rice",
            "quantity": "8",
            "price": "3.25",
            "barcode": "777",
            "category": "Grains",
            "brand": "Lundberg",
            "description": "Brown rice",
        },
        follow_redirects=True,
    )
    assert "Updated Brown Rice." in updated.get_data(as_text=True)
    stored = client.get("/api/inventory/1").get_json()
    assert stored["quantity"] == 8
    assert stored["price"] == 3.25

    deleted = client.post("/items/1/delete", follow_redirects=True)
    assert "Deleted Brown Rice." in deleted.get_data(as_text=True)
    assert client.get("/api/inventory").get_json() == []


def test_admin_shows_external_results_and_imports_them(client, store, monkeypatch):
    monkeypatch.setattr(
        "app.openfoodfacts.requests.get",
        lambda *args, **kwargs: FakeResponse(NUTELLA),
    )
    lookup = client.get("/", query_string={"barcode": "3017620422003"})
    page = lookup.get_data(as_text=True)
    assert "Nutella" in page
    assert "Ferrero" in page
    assert "Add to inventory" in page

    imported = client.post(
        "/import",
        data={"barcode": "3017620422003", "quantity": "2", "price": "5.50", "match_index": "0"},
        follow_redirects=True,
    )
    assert "Imported Nutella into inventory." in imported.get_data(as_text=True)
    assert len(store.records) == 1
    assert store.records[0]["name"] == "Nutella"
    assert store.records[0]["quantity"] == 2
    assert store.records[0]["price"] == 5.5


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
