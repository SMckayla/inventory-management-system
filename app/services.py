"""Lookups that read product details from Open Food Facts."""

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
