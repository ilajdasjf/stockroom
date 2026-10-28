"""Validation and transactional SQLite persistence, independent of the GUI."""
import csv
import sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


COLUMNS = ('sku', 'name', 'category', 'quantity', 'minimum', 'price')


def validate(values):
    result = {k: str(values.get(k, '')).strip() for k in COLUMNS}
    for key in ('sku', 'name', 'category'):
        if not result[key] or len(result[key]) > 100:
            raise ValueError(f'{key.title()} is required and must be 100 characters or fewer.')
    result['sku'] = result['sku'].upper()
    for key in ('quantity', 'minimum'):
        try:
            result[key] = int(result[key])
        except ValueError:
            raise ValueError(f'{key.title()} must be a whole number.') from None
        if not 0 <= result[key] <= 10000000:
            raise ValueError(f'{key.title()} must be between 0 and 10,000,000.')
    try:
        price = Decimal(result['price'])
        if not price.is_finite() or price < 0 or price > 100000000:
            raise InvalidOperation
        if price != price.quantize(Decimal('0.01')):
            raise ValueError('Unit price can have at most two decimal places.')
        result['price'] = int(price * 100)
    except InvalidOperation:
        raise ValueError('Unit price must be a valid non-negative amount.') from None
    return result


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys = ON')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY, sku TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL, category TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity >= 0),
                minimum INTEGER NOT NULL CHECK(minimum >= 0),
                price INTEGER NOT NULL CHECK(price >= 0));
            CREATE TABLE IF NOT EXISTS movements (
                id INTEGER PRIMARY KEY, product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
                product_name TEXT NOT NULL, change INTEGER NOT NULL,
                reason TEXT NOT NULL, created TEXT NOT NULL);
        ''')

    def products(self):
        return [dict(r) for r in self.db.execute('SELECT * FROM products ORDER BY name COLLATE NOCASE')]

    def movements(self):
        return [dict(r) for r in self.db.execute('SELECT * FROM movements ORDER BY id DESC')]

    def _movement(self, product_id, name, change, reason):
        self.db.execute('INSERT INTO movements(product_id, product_name, change, reason, created) VALUES (?,?,?,?,?)',
                        (product_id, name, change, reason, datetime.now().isoformat(timespec='seconds')))

    def _save(self, data, product_id=None):
        old = self.db.execute('SELECT * FROM products WHERE id=?', (product_id,)).fetchone() if product_id else None
        if product_id and old is None:
            raise ValueError('This product no longer exists. Refresh and try again.')
        values = [data[k] for k in COLUMNS]
        if old:
            self.db.execute('UPDATE products SET sku=?,name=?,category=?,quantity=?,minimum=?,price=? WHERE id=?', values + [product_id])
        else:
            product_id = self.db.execute('INSERT INTO products(sku,name,category,quantity,minimum,price) VALUES (?,?,?,?,?,?)', values).lastrowid
        delta = data['quantity'] - (old['quantity'] if old else 0)
        if delta or not old:
            self._movement(product_id, data['name'], delta, 'Product edited' if old else 'Opening stock')
        return product_id

    def save(self, values, product_id=None):
        data = validate(values)
        try:
            with self.db:
                return self._save(data, product_id)
        except sqlite3.IntegrityError:
            raise ValueError('That SKU already exists. Choose a unique SKU.') from None

    def delete(self, product_id):
        with self.db:
            row = self.db.execute('SELECT * FROM products WHERE id=?', (product_id,)).fetchone()
            if row:
                self._movement(product_id, row['name'], -row['quantity'], 'Product deleted')
                self.db.execute('DELETE FROM products WHERE id=?', (product_id,))

    def adjust(self, product_id, change, reason):
        try:
            change = int(str(change).strip())
        except ValueError:
            raise ValueError('Stock change must be a whole number, such as 5 or -2.') from None
        if not change or not reason.strip():
            raise ValueError('Enter a non-zero change and a reason.')
        with self.db:
            row = self.db.execute('SELECT * FROM products WHERE id=?', (product_id,)).fetchone()
            if not row:
                raise ValueError('Select an existing product.')
            if not 0 <= row['quantity'] + change <= 10000000:
                raise ValueError('Resulting stock must be between 0 and 10,000,000.')
            self.db.execute('UPDATE products SET quantity=quantity+? WHERE id=?', (change, product_id))
            self._movement(product_id, row['name'], change, reason.strip())

    def export_csv(self, path):
        with open(path, 'w', newline='', encoding='utf-8-sig') as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            writer.writeheader()
            for row in self.products():
                values = {k: row[k] for k in COLUMNS}
                values['price'] = f"{row['price'] / 100:.2f}"
                writer.writerow(values)

    def import_csv(self, path):
        with open(path, newline='', encoding='utf-8-sig') as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or set(reader.fieldnames) != set(COLUMNS):
                raise ValueError('CSV headers must be: ' + ', '.join(COLUMNS))
            rows = []
            for line, row in enumerate(reader, 2):
                try:
                    rows.append(validate(row))
                except (ValueError, TypeError) as exc:
                    raise ValueError(f'CSV line {line}: {exc}') from exc
                if len(rows) > 10000:
                    raise ValueError('Import at most 10,000 products at a time.')
        try:
            with self.db:
                for row in rows:
                    self._save(row)
        except sqlite3.IntegrityError:
            raise ValueError('Import cancelled: duplicate SKU in the file or inventory. No rows were imported.') from None
        return len(rows)

    def close(self):
        self.db.close()
