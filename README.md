# Inventory Management System

Flask REST API for a small retail shop. Employees can add and view inventory from an administrator portal or a command-line client. Product details can be pulled from [Open Food Facts](https://world.openfoodfacts.org/) by barcode or name and shown beside the inventory. Those catalog results are not written into inventory.

Inventory is stored in a process-local array (`InventoryStore.records`). Restarting the server clears it. The app is meant for local use and does not include authentication.

## Problem

Staff were retyping product names, brands, and categories for items that already exist in a public catalog. They needed one place to record new stock and look at what is on hand. This project is that back-office tool: a JSON API, a small web portal, and a CLI, all sharing the same in-memory inventory. Quantities and prices are set when an item is added. The app does not edit or delete a row afterward, and it does not copy a catalog hit into the inventory array.

## Design

```
cli.py  ----HTTP---->  Flask API  ---->  InventoryStore.records (array)
                         |  \
                         |   \--> Open Food Facts (barcode or name)
                         |
                    Admin portal (/)
```

| Piece | Responsibility |
| --- | --- |
| `app/store.py` | Database array: create and read records |
| `app/routes.py` | JSON API: create, read, and helper routes |
| `app/openfoodfacts.py` | External product lookup |
| `app/services.py` | Barcode and name lookup |
| `app/admin.py` | Portal for adding stock and viewing catalog matches |
| `cli.py` | Calls the REST API from the terminal |

An item looks like this:

```json
{
  "id": 1,
  "name": "Nutella",
  "barcode": "3017620422003",
  "quantity": 6,
  "price": 4.25,
  "category": "Spreads",
  "brand": "Ferrero",
  "description": "Hazelnut cocoa spread",
  "image_url": null
}
```

### Admin portal layout

```
+------------------------------------------------------+
| Inventory Admin                                      |
| Items: 2    Units: 12    Stock value: 21.00          |
+---------------------------+--------------------------+
| Look up a product         | Add an item              |
| Barcode [____________]    | Name, qty, price, brand  |
| Name    [____________]    | [Add to inventory]       |
| [Search Open Food Facts]  |                          |
+---------------------------+--------------------------+
| Results: Nutella · Ferrero · 3017620422003           |
+------------------------------------------------------+
| Current inventory                                    |
| ID  Name     Barcode  Qty  Price  Brand              |
+------------------------------------------------------+
```

## Setup

Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the API and portal

```bash
python run.py
```

The API and the admin portal listen on http://127.0.0.1:5000. Open that address in a browser to use the portal.

Data lives in memory. Stop the process and the inventory is gone.

## Command-line client

Leave the server running, then in another terminal (with the same virtual environment):

```bash
python cli.py list
python cli.py add --name "Green Tea" --quantity 12 --price 3.50 --brand Rishi
python cli.py get 1
python cli.py search tea
python cli.py lookup --barcode 3017620422003
python cli.py lookup --name "oat milk"
```

`lookup` prints catalog matches and does not save them. `list --json` prints the raw response. Point the client at another server with `--base-url http://127.0.0.1:5001`.

`python cli.py serve` starts the same app as `python run.py`.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Liveness check |
| GET | `/api/stats` | Item count, unit count, and stock value |
| GET | `/api/inventory` | List every item |
| GET | `/api/inventory/<id>` | Read one item |
| POST | `/api/inventory` | Create an item |
| GET | `/api/inventory/search?q=` | Search name, barcode, brand, or category |
| GET | `/api/inventory/low-stock?threshold=5` | Items at or below a quantity |
| GET | `/api/external/products?barcode=` | Look up one Open Food Facts product |
| GET | `/api/external/products?name=` | Search Open Food Facts by name |

Create example:

```bash
curl -s -X POST http://127.0.0.1:5000/api/inventory \
  -H "Content-Type: application/json" \
  -d '{"name":"Green Tea","quantity":12,"price":3.5,"brand":"Rishi"}'
```

`name` is required when creating an item. `quantity` and `price` default to 0 and cannot be negative. Prices are stored with two decimal places. A barcode lookup wins when a request includes both a barcode and a name. Lookup responses are not stored.

Open Food Facts asks applications to send a descriptive User-Agent. This app sends `InventoryManagementSystem/1.0 (educational lab)`.

## Tests

```bash
pytest
```

The suite covers the in-memory store, create and read routes, helper routes, Open Food Facts lookup, the admin portal, and the CLI commands that remain. External HTTP calls are mocked, so the suite does not need network access.

## Project layout

```
app/
  __init__.py          app factory
  store.py             in-memory database array
  validation.py        request checks
  openfoodfacts.py     external API client
  services.py          barcode and name lookup
  routes.py            JSON routes
  admin.py             portal routes
  templates/admin.html portal page
cli.py                 terminal client
run.py                 development server
tests/                 unit tests per feature
```

## Maintenance

New item fields need a change in four places: the record built in `InventoryStore.create`, `EDITABLE_FIELDS` in `app/validation.py`, the admin form, and the CLI flags in `cli.py`. Helper reads can stay on `store.all()` and will pick the new field up automatically.

The store is intentionally not a database server. Swap `InventoryStore` for another class with the same methods (`all`, `get`, `create`, `search`, `low_stock`, `stats`) if the inventory needs to survive a restart.
