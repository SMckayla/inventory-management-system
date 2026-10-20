"""Server-rendered administrator portal."""

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from app.openfoodfacts import ExternalAPIError
from app.services import lookup_products
from app.validation import parse_item_payload

admin_bp = Blueprint("admin", __name__)


def _store():
    return current_app.config["INVENTORY"]


@admin_bp.get("/")
def dashboard():
    barcode = request.args.get("barcode", "").strip()
    name = request.args.get("name", "").strip()
    products = []
    if barcode or name:
        try:
            if barcode:
                products, error = lookup_products(barcode=barcode)
            else:
                products, error = lookup_products(name=name)
            if error:
                flash(error, "error")
            elif not products:
                flash("No matching products on Open Food Facts.", "error")
        except ExternalAPIError as exc:
            flash(str(exc), "error")
    return render_template(
        "admin.html",
        items=_store().all(),
        stats=_store().stats(),
        products=products,
        barcode=barcode,
        name=name,
    )


@admin_bp.post("/items")
def create_item():
    payload, error = parse_item_payload(_form_payload())
    if error:
        flash(error, "error")
        return redirect(url_for("admin.dashboard"))
    item = _store().create(payload)
    flash(f"Added {item['name']}.", "success")
    return redirect(url_for("admin.dashboard"))


def _form_payload():
    data = {}
    for field in (
        "name",
        "barcode",
        "quantity",
        "price",
        "category",
        "brand",
        "description",
        "image_url",
    ):
        if field in request.form:
            data[field] = request.form.get(field)
    return data
