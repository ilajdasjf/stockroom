# Project overview: Stockroom

## Objective and users

Stockroom helps a small shop, student club, or office maintain an inventory catalogue, track stock changes, identify low-stock products, and understand inventory value. It is a local desktop GUI application with event-driven interaction.

## Technology and structure

Python 3.10+ provides the runtime, Tkinter/ttk provides native desktop GUI controls, and SQLite provides transactional file-based database storage. All dependencies are included with standard Python installations that include Tk.

The presentation layer handles navigation and user interaction. The store layer owns validation, persistence, import/export, and stock movement consistency. Automated tests exercise the store using temporary databases.

## Requirement mapping

| Assignment requirement | Implementation |
|---|---|
| Main page plus two additional pages | Dashboard plus Inventory, Movements, Reports, Help & About |
| Functional navigation | Persistent sidebar and active page indicator |
| Persistence | SQLite database, loaded on launch and saved per operation |
| CRUD | Product add, table view, edit, confirmed deletion |
| Search and filtering | Text search, category selection, low-stock filter |
| Sorting | Click table column headings; click again to reverse |
| Data display | Scrollable ttk Treeview tables |
| Validation | Required text, unique SKU, bounded integers, decimal prices |
| Events | Button commands, double-click edit, variable-change search, close handling |
| Error handling | Operation dialogs, transaction rollback, startup storage errors |
| Import/export | CSV with header and row validation; atomic import |
| Help/About | Dedicated page with instructions, data location, and version |
| Enhanced functionality | Stock audit history, dashboard, category reports and chart |
| Multi-entity relation | Products referenced by movement records with foreign keys |

## Data model

Products: id, unique sku, name, category, quantity, minimum, price in integer cents.

Movements: id, nullable product_id, product_name snapshot, change, reason, created timestamp. One product has many movements. Product deletion sets the historical foreign key to NULL while retaining the name snapshot and adjustment history.

Low stock means quantity is less than or equal to the minimum. Stock value is quantity multiplied by unit price. This is a stock valuation estimate, not an accounting profit report.

## Reliability

Each mutation runs in a SQLite transaction. Product updates and history writes succeed together. Imports validate all rows first and roll back every insertion on a duplicate. Prices are parsed with Decimal and stored as cents. Parameterized SQL avoids interpolating user input into queries.

## Suggested demonstration

Import the sample catalogue, show dashboard metrics, find a USB cable, adjust its quantity with a reason, inspect movement history, edit a price, show an invalid negative quantity, sort a table, display category reports, export CSV, restart to demonstrate persistence, and open Help.

## Authorship

Enter your name, student number, course, and instructor before submission. If submitting as a team, document each person's actual responsibilities. This implementation was prepared with AI assistance; follow your course's disclosure requirements.
