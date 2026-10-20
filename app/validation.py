"""Validate inventory request payloads."""

import math

TEXT_FIELDS = ("category", "brand", "description", "image_url")


def parse_item_payload(data):
    """Return ``(cleaned, error)`` for a create payload.

    ``cleaned`` holds recognized fields coerced to storage types.
    A missing quantity or price becomes 0.
    """
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object."

    cleaned = {}

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        return None, "name is required."
    cleaned["name"] = name.strip()

    if "barcode" in data:
        barcode, error = _optional_text(data["barcode"], "barcode")
        if error:
            return None, error
        cleaned["barcode"] = barcode

    if "quantity" in data:
        try:
            quantity = _parse_quantity(data["quantity"])
        except (TypeError, ValueError):
            return None, "quantity must be an integer."
        if quantity < 0:
            return None, "quantity cannot be negative."
        cleaned["quantity"] = quantity
    else:
        cleaned["quantity"] = 0

    if "price" in data:
        try:
            price = _parse_price(data["price"])
        except (TypeError, ValueError):
            return None, "price must be a number."
        if price < 0:
            return None, "price cannot be negative."
        cleaned["price"] = price
    else:
        cleaned["price"] = 0.0

    for field in TEXT_FIELDS:
        if field in data:
            text, error = _optional_text(data[field], field)
            if error:
                return None, error
            cleaned[field] = text

    return cleaned, None


def _optional_text(value, field):
    if value is None:
        return None, None
    if not isinstance(value, str):
        return None, f"{field} must be a string."
    return value.strip() or None, None


def _parse_quantity(raw):
    if isinstance(raw, bool):
        raise ValueError
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        if not raw.is_integer():
            raise ValueError
        return int(raw)
    if isinstance(raw, str) and _is_integer_string(raw):
        return int(raw.strip())
    raise ValueError


def _is_integer_string(raw):
    text = raw.strip()
    if text.startswith("-"):
        text = text[1:]
    return text.isdigit()


def _parse_price(raw):
    if isinstance(raw, bool):
        raise ValueError
    if isinstance(raw, (int, float)):
        price = float(raw)
    elif isinstance(raw, str):
        price = float(raw.strip())
    else:
        raise ValueError
    if not math.isfinite(price):
        raise ValueError
    return round(price, 2)
