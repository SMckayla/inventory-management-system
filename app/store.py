"""In-memory inventory database."""


class InventoryStore:
    """Process-local database array of inventory records.

    ``records`` is a list. It lives only as long as the server process.
    Restarting the app clears it.
    """

    def __init__(self):
        self.records = []
        self._next_id = 1

    def all(self):
        """Return a copy of every inventory record."""
        return [record.copy() for record in self.records]

    def get(self, item_id):
        """Return one record, or None when the id is unknown."""
        record = self._find(item_id)
        return None if record is None else record.copy()

    def create(self, data):
        """Append a record to the database array and return a copy."""
        record = {
            "id": self._next_id,
            "name": data["name"],
            "barcode": data.get("barcode"),
            "quantity": int(data.get("quantity", 0)),
            "price": float(data.get("price", 0)),
            "category": data.get("category"),
            "brand": data.get("brand"),
            "description": data.get("description"),
            "image_url": data.get("image_url"),
        }
        self._next_id += 1
        self.records.append(record)
        return record.copy()

    def search(self, query):
        """Case-insensitive match on name, barcode, brand, and category."""
        needle = query.strip().lower()
        if not needle:
            return []
        matches = []
        for record in self.records:
            haystack = " ".join(
                str(record.get(field) or "")
                for field in ("name", "barcode", "brand", "category")
            ).lower()
            if needle in haystack:
                matches.append(record.copy())
        return matches

    def low_stock(self, threshold):
        """Return records whose quantity is at or below ``threshold``."""
        return [
            record.copy()
            for record in self.records
            if record["quantity"] <= threshold
        ]

    def stats(self):
        """Summarize how many items are stored and what they are worth."""
        total_value = sum(record["quantity"] * record["price"] for record in self.records)
        return {
            "count": len(self.records),
            "total_quantity": sum(record["quantity"] for record in self.records),
            "total_value": round(total_value, 2),
        }

    def _find(self, item_id):
        for record in self.records:
            if record["id"] == item_id:
                return record
        return None
