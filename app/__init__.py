"""Inventory management Flask application."""

from flask import Flask

from app.routes import api_bp
from app.store import InventoryStore


def create_app(store=None):
    """Create the Flask app.

    Tests pass their own store so each test gets a private database array.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-inventory-lab"
    app.config["INVENTORY"] = store if store is not None else InventoryStore()
    app.register_blueprint(api_bp)
    return app
