import cli
from cli import ApiError


class FakeClient:
    def __init__(self, base_url, session=None):
        self.base_url = base_url
        self.calls = []

    def list_items(self):
        return [
            {
                "id": 1,
                "name": "Green Tea",
                "barcode": "111",
                "quantity": 3,
                "price": 2.5,
                "brand": "Rishi",
            }
        ]

    def get_item(self, item_id):
        if item_id == 404:
            raise ApiError("Item not found.", 404)
        return {"id": item_id, "name": "Green Tea", "quantity": 3, "price": 2.5}

    def create_item(self, payload):
        self.calls.append(("create", payload))
        return {"id": 2, "name": payload["name"]}

    def search_items(self, query):
        self.calls.append(("search", query))
        return self.list_items()

    def lookup(self, barcode=None, name=None):
        self.calls.append(("lookup", barcode, name))
        if barcode == "missing":
            return {"products": []}
        return {"products": [{"name": "Nutella", "barcode": barcode or "999", "brand": "Ferrero"}]}

    def import_product(self, payload):
        self.calls.append(("import", payload))
        return {
            "id": 4,
            "name": "Nutella",
            "quantity": payload["quantity"],
            "price": payload["price"],
        }


def _install(monkeypatch):
    holder = {}

    def factory(base_url, session=None):
        client = FakeClient(base_url, session=session)
        holder["client"] = client
        return client

    monkeypatch.setattr(cli, "ApiClient", factory)
    return holder


def test_list_and_json_output(monkeypatch, capsys):
    _install(monkeypatch)
    assert cli.main(["list"]) == 0
    assert "Green Tea" in capsys.readouterr().out

    assert cli.main(["list", "--json"]) == 0
    assert '"name": "Green Tea"' in capsys.readouterr().out


def test_get_add_and_search(monkeypatch, capsys):
    holder = _install(monkeypatch)

    assert cli.main(["get", "1"]) == 0
    assert "Green Tea" in capsys.readouterr().out

    assert cli.main(["add", "--name", "Honey", "--quantity", "2", "--price", "6.5"]) == 0
    assert "Created #2 Honey" in capsys.readouterr().out
    assert holder["client"].calls[0][1]["name"] == "Honey"
    assert holder["client"].calls[0][1]["quantity"] == 2

    assert cli.main(["search", "tea"]) == 0
    assert holder["client"].calls[-1] == ("search", "tea")


def test_lookup_and_import(monkeypatch, capsys):
    holder = _install(monkeypatch)

    assert cli.main(["lookup"]) == 1
    assert "barcode" in capsys.readouterr().err

    assert cli.main(["lookup", "--barcode", "3017620422003"]) == 0
    assert "Nutella" in capsys.readouterr().out

    assert cli.main(["lookup", "--barcode", "missing"]) == 0
    assert "No products found." in capsys.readouterr().out

    assert cli.main([
        "import-product",
        "--barcode",
        "3017620422003",
        "--quantity",
        "2",
        "--price",
        "4.99",
    ]) == 0
    assert "Imported #4 Nutella" in capsys.readouterr().out
    imported = holder["client"].calls[-1][1]
    assert imported["barcode"] == "3017620422003"
    assert imported["quantity"] == 2
    assert imported["price"] == 4.99

    assert cli.main(["import-product", "--quantity", "1"]) == 1


def test_api_errors_use_a_nonzero_exit_code(monkeypatch, capsys):
    _install(monkeypatch)
    assert cli.main(["get", "404"]) == 1
    assert "Item not found." in capsys.readouterr().err


def test_parser_accepts_serve_and_a_custom_base_url():
    args = cli.build_parser().parse_args(["--base-url", "http://localhost:5001", "serve"])
    assert args.command == "serve"
    assert args.base_url == "http://localhost:5001"
