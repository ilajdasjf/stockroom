"""Exercise real Tk widgets without modifying the user's database."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stockroom.app import Application
from stockroom.store import Store

with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as folder:
    store = Store(Path(folder) / 'gui.db')
    store.import_csv(Path(__file__).resolve().parents[1] / 'sample_inventory.csv')
    app = Application(store)
    app.update()
    for page in ('Dashboard', 'Inventory', 'Movements', 'Reports', 'Help & About'):
        app.show(page)
        app.update()
        print('Rendered:', page)
    app.show('Inventory')
    assert len(app.tree.get_children()) == 8
    app.search.set('USB-C')
    assert len(app.tree.get_children()) == 1
    app.search.set('')
    app.low.set(True)
    app.refresh_inventory()
    assert len(app.tree.get_children()) == 3
    app.low.set(False)
    app.category.set('Office')
    assert len(app.tree.get_children()) == 3
    app.sort_tree(app.tree, 'Quantity')
    assert [int(app.tree.set(item, 'Quantity')) for item in app.tree.get_children()] == [8, 18, 35]
    app.editor(store.products()[0])
    app.update()
    for child in app.winfo_children():
        if child.winfo_class() == 'Toplevel':
            child.destroy()
    app.close()
    print('PASS: navigation, live search, category/low-stock filters, numeric sorting, editor rendering')
