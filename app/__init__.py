"""Inventory management Flask application."""

from flask import Flask, jsonify


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    return app
