import pytest

from app import create_app
from app.store import InventoryStore


@pytest.fixture
def store():
    return InventoryStore()


@pytest.fixture
def client(store):
    app = create_app(store=store)
    app.config["TESTING"] = True
    return app.test_client()
