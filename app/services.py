"""Operations that combine the inventory store with Open Food Facts."""

from app.openfoodfacts import fetch_by_barcode, search_by_name


def lookup_products(barcode=None, name=None):
    """Look up products by barcode or by name.

    A barcode lookup returns a list of zero or one product.
    Returns ``(products, error)``.
    """
    if barcode:
        product = fetch_by_barcode(barcode)
        return ([product] if product else []), None
    if name:
        return search_by_name(name), None
    return [], "Provide a barcode or a product name."


def import_product(store, barcode=None, name=None, quantity=0, price=0.0, match_index=0):
    """Fetch a product and append it to the inventory database array.

    When both a barcode and a name are given, the barcode wins.
    ``match_index`` selects a hit from a name search.
    Returns ``(item, error)``.
    """
    if barcode:
        product = fetch_by_barcode(barcode)
        if product is None:
            return None, "No Open Food Facts product found for that barcode."
    elif name:
        matches = search_by_name(name)
        if not matches:
            return None, "No Open Food Facts products found for that name."
        if match_index < 0 or match_index >= len(matches):
            return None, "match_index is out of range for the search results."
        product = matches[match_index]
    else:
        return None, "Provide a barcode or a product name."

    item = store.create(
        {
            "name": product["name"],
            "barcode": product.get("barcode"),
            "quantity": quantity,
            "price": price,
            "category": product.get("category"),
            "brand": product.get("brand"),
            "description": product.get("description"),
            "image_url": product.get("image_url"),
        }
    )
    return item, None
