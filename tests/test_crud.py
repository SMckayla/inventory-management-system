def test_list_is_empty_at_first(client):
    response = client.get("/api/inventory")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_and_read(client):
    created = client.post(
        "/api/inventory",
        json={
            "name": "  Cocoa  ",
            "quantity": 4,
            "price": 2.5,
            "brand": "Equal Exchange",
            "barcode": "555",
        },
    )
    assert created.status_code == 201
    item = created.get_json()
    assert item["id"] == 1
    assert item["name"] == "Cocoa"
    assert item["quantity"] == 4

    fetched = client.get("/api/inventory/1")
    assert fetched.status_code == 200
    assert fetched.get_json()["brand"] == "Equal Exchange"
    listed = client.get("/api/inventory")
    assert listed.status_code == 200
    assert [row["id"] for row in listed.get_json()] == [1]


def test_create_rejects_a_missing_or_blank_name(client):
    missing = client.post("/api/inventory", json={"quantity": 1})
    assert missing.status_code == 400
    assert "name" in missing.get_json()["error"]

    blank = client.post("/api/inventory", json={"name": "   "})
    assert blank.status_code == 400


def test_create_rejects_bad_numbers_and_non_json(client):
    negative = client.post("/api/inventory", json={"name": "Tea", "quantity": -1})
    assert negative.status_code == 400
    assert "quantity" in negative.get_json()["error"]

    price = client.post("/api/inventory", json={"name": "Tea", "price": "abc"})
    assert price.status_code == 400

    empty = client.post("/api/inventory", data="not-json", content_type="text/plain")
    assert empty.status_code == 400


def test_price_is_rounded_and_string_numbers_are_accepted(client):
    response = client.post(
        "/api/inventory",
        json={"name": "Honey", "quantity": "2", "price": "3.456"},
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["quantity"] == 2
    assert body["price"] == 3.46
