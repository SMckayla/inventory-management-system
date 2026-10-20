"""JSON routes for inventory CRUD and stock helpers."""

from flask import Blueprint, current_app, jsonify, request

from app.validation import parse_item_payload

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _store():
    return current_app.config["INVENTORY"]


@api_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@api_bp.get("/stats")
def stats():
    return jsonify(_store().stats())


@api_bp.get("/inventory")
def list_inventory():
    return jsonify(_store().all())


@api_bp.get("/inventory/search")
def search_inventory():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Query parameter q is required."}), 400
    return jsonify(_store().search(query))


@api_bp.get("/inventory/low-stock")
def low_stock():
    raw_threshold = request.args.get("threshold", "5")
    try:
        threshold = int(raw_threshold)
    except (TypeError, ValueError):
        return jsonify({"error": "threshold must be an integer."}), 400
    if threshold < 0:
        return jsonify({"error": "threshold cannot be negative."}), 400
    return jsonify(_store().low_stock(threshold))


@api_bp.get("/inventory/<int:item_id>")
def get_item(item_id):
    item = _store().get(item_id)
    if item is None:
        return jsonify({"error": "Item not found."}), 404
    return jsonify(item)


@api_bp.post("/inventory")
def create_item():
    payload, error = parse_item_payload(request.get_json(silent=True))
    if error:
        return jsonify({"error": error}), 400
    return jsonify(_store().create(payload)), 201


@api_bp.patch("/inventory/<int:item_id>")
def update_item(item_id):
    payload, error = parse_item_payload(request.get_json(silent=True), partial=True)
    if error:
        return jsonify({"error": error}), 400
    item = _store().update(item_id, payload)
    if item is None:
        return jsonify({"error": "Item not found."}), 404
    return jsonify(item)


@api_bp.delete("/inventory/<int:item_id>")
def delete_item(item_id):
    item = _store().delete(item_id)
    if item is None:
        return jsonify({"error": "Item not found."}), 404
    return jsonify({"deleted": item})
