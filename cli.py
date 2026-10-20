"""Command-line interface for the inventory management API."""

import argparse
import json
import sys

import requests

from app import create_app


class ApiError(Exception):
    """The inventory API returned an error or could not be reached."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class ApiClient:
    """Small HTTP client for the inventory REST API."""

    def __init__(self, base_url, session=None):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()

    def list_items(self):
        return self._request("GET", "/api/inventory")

    def get_item(self, item_id):
        return self._request("GET", f"/api/inventory/{item_id}")

    def create_item(self, payload):
        return self._request("POST", "/api/inventory", json=payload)

    def search_items(self, query):
        return self._request("GET", "/api/inventory/search", params={"q": query})

    def lookup(self, barcode=None, name=None):
        params = {}
        if barcode:
            params["barcode"] = barcode
        if name:
            params["name"] = name
        return self._request("GET", "/api/external/products", params=params)

    def _request(self, method, path, **kwargs):
        try:
            response = self.session.request(
                method,
                f"{self.base_url}{path}",
                timeout=15,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise ApiError(
                f"Could not reach the API at {self.base_url}. Start it with: python run.py"
            ) from exc
        if response.status_code >= 400:
            raise ApiError(_error_message(response), response.status_code)
        if not response.content:
            return None
        return response.json()


def build_parser():
    parser = argparse.ArgumentParser(description="Inventory management CLI")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:5000",
        help="Inventory API base URL (default: http://127.0.0.1:5000)",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("serve", help="Start the API and admin portal")

    list_cmd = commands.add_parser("list", help="List inventory items")
    list_cmd.add_argument("--json", action="store_true", help="Print raw JSON")

    get_cmd = commands.add_parser("get", help="Show one inventory item")
    get_cmd.add_argument("id", type=int)

    add_cmd = commands.add_parser("add", help="Create an inventory item")
    _item_flags(add_cmd)

    search_cmd = commands.add_parser("search", help="Search stored inventory")
    search_cmd.add_argument("query")

    lookup_cmd = commands.add_parser("lookup", help="Fetch product details from Open Food Facts")
    lookup_cmd.add_argument("--barcode")
    lookup_cmd.add_argument("--name")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "serve":
        create_app().run(host="127.0.0.1", port=5000, debug=True)
        return 0
    client = ApiClient(args.base_url)
    try:
        return _dispatch(client, args)
    except ApiError as exc:
        print(exc, file=sys.stderr)
        return 1


def _dispatch(client, args):
    if args.command == "list":
        items = client.list_items()
        if args.json:
            print(json.dumps(items, indent=2))
        else:
            _print_table(items)
        return 0

    if args.command == "get":
        print(json.dumps(client.get_item(args.id), indent=2))
        return 0

    if args.command == "add":
        item = client.create_item(_payload_from_args(args))
        print(f"Created #{item['id']} {item['name']}")
        return 0

    if args.command == "search":
        _print_table(client.search_items(args.query))
        return 0

    if args.command == "lookup":
        if not args.barcode and not args.name:
            print("Provide --barcode or --name.", file=sys.stderr)
            return 1
        result = client.lookup(barcode=args.barcode, name=args.name)
        products = result.get("products") or []
        if not products:
            print("No products found.")
            return 0
        print(json.dumps(products, indent=2))
        return 0

    print(f"Unknown command: {args.command}", file=sys.stderr)
    return 1


def _item_flags(parser):
    parser.add_argument("--name", required=True)
    parser.add_argument("--quantity", type=int)
    parser.add_argument("--price", type=float)
    parser.add_argument("--barcode")
    parser.add_argument("--category")
    parser.add_argument("--brand")
    parser.add_argument("--description")


def _payload_from_args(args):
    payload = {}
    for field in ("name", "quantity", "price", "barcode", "category", "brand", "description"):
        value = getattr(args, field, None)
        if value is not None:
            payload[field] = value
    return payload


def _print_table(items):
    if not items:
        print("No inventory items.")
        return
    headers = ("ID", "Name", "Barcode", "Qty", "Price", "Brand")
    rows = [
        (
            str(item["id"]),
            str(item["name"]),
            item.get("barcode") or "-",
            str(item["quantity"]),
            f"{float(item['price']):.2f}",
            item.get("brand") or "-",
        )
        for item in items
    ]
    widths = [len(header) for header in headers]
    for row in rows:
        widths = [max(widths[index], len(row[index])) for index in range(len(headers))]

    def format_row(row):
        return "  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))

    print(format_row(headers))
    print(format_row(tuple("-" * width for width in widths)))
    for row in rows:
        print(format_row(row))


def _error_message(response):
    try:
        body = response.json()
    except ValueError:
        body = None
    if isinstance(body, dict) and body.get("error"):
        return str(body["error"])
    return f"Request failed with status {response.status_code}."


if __name__ == "__main__":
    sys.exit(main())
