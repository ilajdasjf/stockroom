# Stockroom user guide

## Start and sample data

1. Double-click `Start Stockroom.bat`.
2. Select Inventory from the sidebar.
3. Click Import CSV and choose `sample_inventory.csv` for demonstration data. Import it only once: duplicate SKUs are rejected.

## Add, find, edit, and delete

Click Add product. Supply a unique SKU, product name, category, quantity, minimum stock, and price. Use whole numbers from 0 to 10,000,000 for quantities and up to two decimal places for price. Click Save product. Cancel or Escape closes a dialog without saving.

Type in the inventory search field to search SKU, name, or category. Combine this with the category dropdown and Low stock only checkbox. Clear the text, select All categories, and clear the checkbox to reset filters.

Click a column header to sort; click again to reverse. Select a row and choose Edit, or double-click the row. The action buttons are above the table. Select the red Delete button to remove a product after confirmation. Its movement history remains available.

## Adjust stock

Select a product, click Adjust stock, and enter a signed whole number. Use `5` for five received units or `-2` for two issued units. Enter a reason, such as Delivery or Customer order. The app rejects any adjustment that would result in negative stock.

## Dashboard, movements, reports

Dashboard shows product count, total units, total inventory value, low-stock count, and a reorder watchlist. Movements lists newest stock changes first. Reports groups products by category and charts the top five categories by stock value. Choose one currency for the entire catalogue.

## CSV import and export

Export CSV writes every current product, regardless of active filters. The file contains these headers:

```text
sku,name,category,quantity,minimum,price
```

Import CSV adds new products. It does not update or replace existing SKUs. Use a decimal point for prices and UTF-8 encoding. Import accepts at most 10,000 products. Invalid rows or duplicate SKUs cancel the import without adding any products. A CSV export does not include the movement audit trail.

## Storage and recovery

Changes save automatically. Close the app and copy `data/stockroom.db` to back up all data, including movement history. To restore, close Stockroom and replace that file with your backup. Keep backups separate from the project directory. An optional `STOCKROOM_DATA_DIR` environment variable changes the storage folder.

If startup reports a storage error, check that the storage directory is writable. If an import fails, read the error, correct the file, and retry. If Python is not found, install Python with Tk support and enable its PATH option.
