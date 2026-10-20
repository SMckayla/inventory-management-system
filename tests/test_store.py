from app.store import InventoryStore


def _item(**overrides):
    data = {
        "name": "Green Tea",
        "barcode": "111",
        "quantity": 5,
        "price": 3.5,
        "category": "Tea",
        "brand": "Rishi",
        "description": "Loose leaf",
    }
    data.update(overrides)
    return data


def test_records_array_starts_empty():
    store = InventoryStore()
    assert store.records == []
    assert store.all() == []


def test_create_appends_to_the_database_array():
    store = InventoryStore()
    created = store.create(_item())
    assert created["id"] == 1
    assert created["name"] == "Green Tea"
    assert len(store.records) == 1
    assert store.records[0]["barcode"] == "111"


def test_ids_keep_incrementing_after_delete():
    store = InventoryStore()
    first = store.create(_item())
    store.delete(first["id"])
    second = store.create(_item(name="Oolong"))
    assert second["id"] == 2
    assert [record["name"] for record in store.records] == ["Oolong"]


def test_get_update_and_delete():
    store = InventoryStore()
    created = store.create(_item())
    assert store.get(created["id"])["name"] == "Green Tea"
    updated = store.update(created["id"], {"quantity": 2, "price": 4})
    assert updated["quantity"] == 2
    assert updated["price"] == 4
    assert updated["name"] == "Green Tea"
    removed = store.delete(created["id"])
    assert removed["id"] == created["id"]
    assert store.get(created["id"]) is None
    assert store.delete(created["id"]) is None
    assert store.update(created["id"], {"name": "Missing"}) is None


def test_search_matches_name_brand_and_barcode():
    store = InventoryStore()
    store.create(_item())
    store.create(_item(name="Oat Milk", barcode="222", brand="Oatly", category="Dairy"))
    assert [item["name"] for item in store.search("tea")] == ["Green Tea"]
    assert [item["name"] for item in store.search("oatly")] == ["Oat Milk"]
    assert [item["barcode"] for item in store.search("222")] == ["222"]
    assert store.search("   ") == []


def test_low_stock_and_stats():
    store = InventoryStore()
    store.create(_item(quantity=2, price=3))
    store.create(_item(name="Rice", quantity=10, price=1.5))
    assert [item["name"] for item in store.low_stock(5)] == ["Green Tea"]
    assert store.stats() == {"count": 2, "total_quantity": 12, "total_value": 21.0}
