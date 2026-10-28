import tempfile
import unittest
from pathlib import Path
from stockroom.store import Store


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.path = Path(self.temp.name) / 'test.db'
        self.store = Store(self.path)
        self.product = dict(sku='abc', name='Notebook', category='Office', quantity='5', minimum='2', price='3.25')

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_crud_and_restart(self):
        key = self.store.save(self.product)
        self.store.save(dict(self.product, name='Updated', quantity='8'), key)
        self.store.close()
        self.store = Store(self.path)
        self.assertEqual(self.store.products()[0]['name'], 'Updated')
        self.assertEqual(self.store.products()[0]['price'], 325)
        self.store.delete(key)
        self.assertEqual(self.store.products(), [])
        self.assertEqual([m['change'] for m in self.store.movements()], [-8, 3, 5])
        self.assertTrue(all(m['product_id'] is None for m in self.store.movements()))

    def test_validation(self):
        for change in [dict(sku=''), dict(name=''), dict(quantity='-1'), dict(minimum='2.5'), dict(price='NaN'), dict(price='1.001'), dict(price='bad')]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.store.save(dict(self.product, **change))
        self.assertEqual(self.store.products(), [])

    def test_duplicate_and_negative_stock_rollback(self):
        key = self.store.save(self.product)
        with self.assertRaises(ValueError):
            self.store.save(self.product)
        with self.assertRaises(ValueError):
            self.store.adjust(key, '-6', 'Issue')
        self.assertEqual(self.store.products()[0]['quantity'], 5)
        self.assertEqual(len(self.store.movements()), 1)
        self.store.adjust(key, '-2', 'Customer order')
        self.assertEqual(self.store.products()[0]['quantity'], 3)

    def test_csv_round_trip(self):
        key = self.store.save(self.product)
        path = Path(self.temp.name) / 'export.csv'
        self.store.export_csv(path)
        self.store.delete(key)
        self.assertEqual(self.store.import_csv(path), 1)
        self.assertEqual(self.store.products()[0]['price'], 325)

    def test_import_is_atomic(self):
        self.store.save(self.product)
        path = Path(self.temp.name) / 'import.csv'
        path.write_text('sku,name,category,quantity,minimum,price\nNEW,Pen,Office,4,1,2.00\nABC,Duplicate,Office,1,1,1.00\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.store.import_csv(path)
        self.assertEqual(len(self.store.products()), 1)
        self.assertEqual(len(self.store.movements()), 1)

    def test_invalid_import_does_not_write(self):
        path = Path(self.temp.name) / 'import.csv'
        path.write_text('sku,name,category,quantity,minimum,price\nNEW,Pen,Office,4,1,2.00\nBAD,Bad,Office,-1,1,1.00\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'line 3'):
            self.store.import_csv(path)
        self.assertEqual(self.store.products(), [])


if __name__ == '__main__':
    unittest.main()
