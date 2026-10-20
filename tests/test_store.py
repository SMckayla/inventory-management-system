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


def test_ids_increase_for_each_create():
    store = InventoryStore()
    first = store.create(_item())
    second = store.create(_item(name="Oolong"))
    assert first["id"] == 1
    assert second["id"] == 2
    assert [record["name"] for record in store.records] == ["Green Tea", "Oolong"]


def test_get_returns_a_copy():
    store = InventoryStore()
    created = store.create(_item())
    fetched = store.get(created["id"])
    assert fetched["name"] == "Green Tea"
    fetched["name"] = "Changed"
    assert store.records[0]["name"] == "Green Tea"
    assert store.get(999) is None


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
