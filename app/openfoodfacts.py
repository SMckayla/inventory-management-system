"""Client for the Open Food Facts product API.

https://world.openfoodfacts.org/data
"""

import requests

API_BASE = "https://world.openfoodfacts.org"
USER_AGENT = "InventoryManagementSystem/1.0 (educational lab)"
TIMEOUT_SECONDS = 10


class ExternalAPIError(Exception):
    """Raised when Open Food Facts cannot be reached or returns an error."""


def fetch_by_barcode(barcode):
    """Return one normalized product, or None when the barcode is unknown."""
    barcode = str(barcode).strip()
    if not barcode:
        return None
    payload = _read_json(_request(f"{API_BASE}/api/v2/product/{barcode}.json"))
    if not payload or payload.get("status") != 1:
        return None
    return _normalize(payload.get("product") or {})


def search_by_name(name, page_size=5):
    """Return normalized products whose name matches the search text."""
    name = str(name).strip()
    if not name:
        return []
    payload = _read_json(
        _request(
            f"{API_BASE}/cgi/search.pl",
            params={
                "search_terms": name,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page_size": page_size,
            },
        )
    )
    if not payload:
        return []
    return [_normalize(product) for product in payload.get("products") or []]


def _request(url, params=None):
    try:
        return requests.get(
            url,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise ExternalAPIError("Open Food Facts is unavailable.") from exc


def _read_json(response):
    if response.status_code == 404:
        return None
    try:
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise ExternalAPIError("Open Food Facts is unavailable.") from exc
    except ValueError as exc:
        raise ExternalAPIError("Open Food Facts returned an unreadable response.") from exc


def _normalize(product):
    raw_name = product.get("product_name") or product.get("product_name_en") or ""
    name = raw_name.strip() if isinstance(raw_name, str) else ""
    categories = product.get("categories") or ""
    category = categories.split(",")[0].strip() or None
    description = product.get("generic_name") or product.get("ingredients_text")
    if isinstance(description, str):
        description = description.strip() or None
        if description and len(description) > 500:
            description = description[:497] + "..."
    else:
        description = None
    code = product.get("code")
    return {
        "name": name or "Unknown product",
        "barcode": str(code).strip() if code else None,
        "brand": _clean(product.get("brands")),
        "category": category,
        "description": description,
        "image_url": _clean(product.get("image_front_url") or product.get("image_url")),
    }


def _clean(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None
