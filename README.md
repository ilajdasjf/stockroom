# Stockroom — Visual Programming Project

A desktop inventory manager built with Python, Tkinter/ttk, and SQLite. No third-party packages are required. The assignment permits any GUI framework; this project uses Tkinter rather than Windows Forms or MAUI.

## Run

Install Python 3.10+ with Tk support. On this computer, Python 3.12 and Tk 8.6 are available.

Double-click **Start Stockroom.bat**, or run:

```powershell
python main.py
```

The first launch creates an empty database in `data/stockroom.db`. Import `sample_inventory.csv` from Inventory for a populated demonstration. Use the same currency for every product; amounts are displayed without a currency symbol.

## Features

- Five navigable pages: Dashboard, Inventory, Movements, Reports, Help & About.
- Product CRUD, modal editor, unique SKU validation, quantity and price validation.
- Search across SKU/name/category, category filter, low-stock filter, sortable columns.
- Stock receipt/issue with reasons and a persistent movement audit trail.
- Dashboard metrics and category value chart and summary table.
- Atomic CSV import and complete inventory CSV export.
- SQLite transactions, parameterized queries, foreign keys, integer monetary storage.
- Friendly operation errors, deletion confirmation, automatic persistence.

## Verification

```powershell
python -m unittest discover -s tests -v
python tests/gui_smoke.py
```

See [project overview](docs/PROJECT_OVERVIEW.md), [user guide](docs/USER_GUIDE.md), [code explanation](docs/CODE_EXPLANATION.md), and [submission checklist](docs/SUBMISSION.md).

## Repository

The full runnable source is in this folder. To submit, create a GitHub repository, push this project, and paste its real URL into the submission. No GitHub repository URL is claimed until one has actually been created.

## Limitations

Designed for a single user and a moderate local catalogue. CSV imports are capped at 10,000 rows and run synchronously. Larger datasets would benefit from background workers and paginated queries. It does not include authentication, cloud sync, taxes, or currency conversion. Deletion preserves stock movement history; CSV exports contain current products only. Back up the SQLite database to preserve the full history.
