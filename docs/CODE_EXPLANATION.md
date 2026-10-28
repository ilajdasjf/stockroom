# Code explanation and defense notes

## Main modules

`main.py` is the entry point. It calls `stockroom.app.main`, which chooses the database location, handles startup storage errors, constructs the store and GUI, and starts Tk's event loop.

`stockroom/app.py` defines `Application`, a Tk root window. `show` rebuilds the content area for the selected page. Each page has its own method. The reusable `table` method creates a Treeview with scrollbars and sortable headings. `editor` and `adjust` create modal dialogs.

`stockroom/store.py` defines `Store`, the data-access and business-logic boundary. It creates the SQLite schema, retrieves rows, validates changes, updates products, logs movements, and imports/exports CSV. The standalone `validate` function normalizes SKU/text fields and validates numbers.

`tests/test_store.py` verifies CRUD and restart persistence, input validation, duplicate prevention, negative-stock protection, CSV round trips, and atomic import behavior.

## Event flow

1. A user clicks Save product.
2. The dialog callback reads its StringVar values.
3. Store.save validates the values before opening a transaction.
4. The store inserts or updates the product and writes a quantity-change record.
5. SQLite commits both changes, or rolls them back together on failure.
6. The dialog closes and the current page refreshes.

Search is event-driven: StringVar traces refresh the table whenever search/category values change. The low-stock checkbox invokes the same refresh method. Double-click bindings open the selected product. The root window close event closes the database connection before destroying the application.

## Design decisions

- SQLite needs no database server and supports relationships and transactions.
- Integer cents prevent binary floating-point errors in stored prices.
- Decimal parses user prices without silently accepting a third decimal place.
- SQL parameters keep input values separate from SQL syntax.
- Stock history snapshots the product name so deletion does not erase context.
- Import validates the entire file before writing; one transaction protects against partial imports.
- Direct SQL is used instead of an ORM to keep the project dependency-free and easy to explain.

## Likely defense questions

**Where is data saved?** In the local `data/stockroom.db` SQLite file, with optional location override.

**How is partial import prevented?** Rows validate first, and every insertion shares one transaction. Constraint failures roll back the transaction.

**What distinguishes editing from adjustment?** Editing updates catalogue fields and logs quantity differences. Adjustment records a signed quantity change and a user-supplied reason.

**Why is history retained after deletion?** The movement foreign key uses ON DELETE SET NULL, and the movement holds a product-name snapshot.

**How could this grow?** Split presentation into page classes as complexity grows; add worker-thread imports, pagination, supplier entities, barcode input, and packaging. The current application targets a moderate single-user catalogue.
