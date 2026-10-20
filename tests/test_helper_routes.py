def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_stats_follow_creates(client):
    assert client.get("/api/stats").get_json()["count"] == 0
    client.post("/api/inventory", json={"name": "Rice", "quantity": 3, "price": 2})
    client.post("/api/inventory", json={"name": "Beans", "quantity": 1, "price": 4})
    assert client.get("/api/stats").get_json() == {
        "count": 2,
        "total_quantity": 4,
        "total_value": 10.0,
    }


def test_search_route(client):
    client.post("/api/inventory", json={"name": "Green Tea", "brand": "Rishi", "barcode": "111"})
    client.post("/api/inventory", json={"name": "Coffee", "brand": "Stumptown"})

    missing_query = client.get("/api/inventory/search")
    assert missing_query.status_code == 400

    found = client.get("/api/inventory/search", query_string={"q": "rishi"})
    assert found.status_code == 200
    assert [item["name"] for item in found.get_json()] == ["Green Tea"]


def test_low_stock_route(client):
    client.post("/api/inventory", json={"name": "Tea", "quantity": 1, "price": 2})
    client.post("/api/inventory", json={"name": "Rice", "quantity": 20, "price": 1})

    default = client.get("/api/inventory/low-stock")
    assert [item["name"] for item in default.get_json()] == ["Tea"]

    custom = client.get("/api/inventory/low-stock", query_string={"threshold": 0})
    assert custom.get_json() == []

    invalid = client.get("/api/inventory/low-stock", query_string={"threshold": "many"})
    assert invalid.status_code == 400

    negative = client.get("/api/inventory/low-stock", query_string={"threshold": -1})
    assert negative.status_code == 400
