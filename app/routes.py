"""JSON routes for inventory CRUD and Open Food Facts lookup."""

from flask import Blueprint, current_app, jsonify, request

from app.openfoodfacts import ExternalAPIError
from app.services import import_product, lookup_products
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


@api_bp.get("/external/products")
def external_products():
    barcode = request.args.get("barcode", "").strip()
    name = request.args.get("name", "").strip()
    if not barcode and not name:
        return jsonify({"error": "Provide a barcode or a name."}), 400
    try:
        if barcode:
            products, error = lookup_products(barcode=barcode)
        else:
            products, error = lookup_products(name=name)
    except ExternalAPIError as exc:
        return jsonify({"error": str(exc)}), 502
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"source": "openfoodfacts", "products": products})


@api_bp.post("/inventory/import")
def import_inventory():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    stock, error = parse_item_payload(
        {
            "name": "pending import",
            "quantity": body.get("quantity", 0),
            "price": body.get("price", 0),
        }
    )
    if error:
        return jsonify({"error": error}), 400

    try:
        match_index = _match_index(body.get("match_index", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "match_index must be an integer."}), 400

    try:
        item, error = import_product(
            _store(),
            barcode=_optional_identifier(body.get("barcode")),
            name=_optional_identifier(body.get("name")),
            quantity=stock["quantity"],
            price=stock["price"],
            match_index=match_index,
        )
    except ExternalAPIError as exc:
        return jsonify({"error": str(exc)}), 502

    if error:
        status = 404 if error.startswith("No Open Food Facts") else 400
        return jsonify({"error": error}), status
    return jsonify(item), 201


def _optional_identifier(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _match_index(raw):
    if isinstance(raw, bool):
        raise ValueError
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str) and raw.strip().lstrip("-").isdigit():
        return int(raw.strip())
    raise ValueError
