"""Event-driven Tkinter presentation layer."""
import csv
import os
import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from .store import Store, COLUMNS

BG = '#f5f5f9'
NAV = '#191a2e'
BLUE = '#7460e8'
INK = '#25263d'
MUTED = '#85869a'


class Application(tk.Tk):
    def __init__(self, store):
        super().__init__()
        self.store = store
        self.title('Stockroom | Inventory Studio')
        self.geometry('1240x780')
        self.minsize(960, 640)
        self.configure(bg=BG)
        self.protocol('WM_DELETE_WINDOW', self.close)
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 10), background=BG)
        style.configure('TButton', padding=(15, 9), background='white', foreground=INK, borderwidth=0)
        style.map('TButton', background=[('active', '#ebe7ff')])
        style.configure('Primary.TButton', background=BLUE, foreground='white')
        style.map('Primary.TButton', background=[('active', '#5e49cd')])
        style.configure('Danger.TButton', foreground='#b42337', background='#fff0f2')
        style.map('Danger.TButton', background=[('active', '#ffe0e5')])
        style.configure('TEntry', padding=9, bordercolor='#e4e3ee', lightcolor='white', fieldbackground='white')
        style.configure('TCombobox', padding=8, bordercolor='#e4e3ee', arrowsize=13)
        style.configure('Treeview', background='white', fieldbackground='white', foreground=INK, rowheight=43, borderwidth=0)
        style.configure('Treeview.Heading', padding=12, background='#f0eff7', foreground='#77788d', relief='flat', font=('Segoe UI', 9, 'bold'))
        style.map('Treeview', background=[('selected', BLUE)])
        nav = tk.Frame(self, bg=NAV, width=210)
        nav.pack(side='left', fill='y')
        nav.pack_propagate(False)
        tk.Label(nav, text='◈  stockroom', bg=NAV, fg='white', font=('Segoe UI', 20, 'bold')).pack(padx=22, pady=(28, 4), anchor='w')
        tk.Label(nav, text='YOUR INVENTORY, IN ORDER', bg=NAV, fg='#767893', font=('Segoe UI', 8)).pack(padx=24, pady=(0, 35), anchor='w')
        tk.Label(nav, text='WORKSPACE', bg=NAV, fg='#6e708d', font=('Segoe UI', 8, 'bold')).pack(padx=24, pady=(0, 12), anchor='w')
        self.nav_buttons = {}
        icons = ('▦', '▤', '⇄', '▥', '?')
        for icon, name in zip(icons, ('Dashboard', 'Inventory', 'Movements', 'Reports', 'Help & About')):
            button = tk.Button(nav, text=f'{icon}    {name}', anchor='w', bg=NAV, fg='#a5a7bf', relief='flat', bd=0,
                               activebackground=BLUE, activeforeground='white', font=('Segoe UI', 11), padx=20, pady=13,
                               command=lambda page=name: self.show(page))
            button.pack(fill='x', padx=10, pady=3)
            self.nav_buttons[name] = button
        profile = tk.Frame(nav, bg='#22233b', padx=16, pady=15)
        profile.pack(side='bottom', fill='x', padx=14, pady=20)
        tk.Label(profile, text='●  Personal workspace', bg='#22233b', fg='#deddf1', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        tk.Label(profile, text='Local edition  /  v1.0', bg='#22233b', fg='#82849f', font=('Segoe UI', 9)).pack(anchor='w', pady=(5, 0))
        top = tk.Frame(self, bg='white', height=58)
        top.pack(side='top', fill='x')
        top.pack_propagate(False)
        self.breadcrumb = tk.StringVar()
        tk.Label(top, textvariable=self.breadcrumb, bg='white', fg=MUTED, font=('Segoe UI', 10)).pack(side='left', padx=28)
        tk.Label(top, text='●  All changes saved     |     My workspace', bg='white', fg='#7a8293', font=('Segoe UI', 9)).pack(side='right', padx=28)
        self.content = tk.Frame(self, bg=BG)
        self.status = tk.StringVar(value='Ready • Your changes are saved automatically')
        tk.Label(self, textvariable=self.status, bg=BG, fg='#607087', anchor='w').pack(side='bottom', fill='x', padx=28, pady=8)
        self.content.pack(side='top', fill='both', expand=True, padx=28, pady=24)
        self.show('Dashboard')

    def report_callback_exception(self, exc_type, value, traceback):
        messagebox.showerror('Something went wrong', f'The operation could not be completed.\n{value}', parent=self)

    def close(self):
        self.store.close()
        self.destroy()

    def label(self, parent, text, size=11, color='#15243a', bold=False):
        widget = tk.Label(parent, text=text, bg=parent.cget('bg'), fg=color, font=('Segoe UI', size, 'bold' if bold else 'normal'), anchor='w', justify='left')
        widget.pack(anchor='w', pady=(0, 10))
        return widget

    def show(self, page):
        self.page = page
        self.breadcrumb.set(f'Workspace   /   {page}')
        for widget in self.content.winfo_children():
            widget.destroy()
        for name, button in self.nav_buttons.items():
            button.configure(bg=BLUE if name == page else NAV, fg='white' if name == page else '#a5a7bf')
        heading = tk.Frame(self.content, bg=BG)
        heading.pack(fill='x')
        if page == 'Dashboard':
            ttk.Button(heading, text='+  Add product', style='Primary.TButton', command=self.editor).pack(side='right', pady=4)
        self.label(heading, 'Inventory overview' if page == 'Dashboard' else page, 25, INK, bold=True)
        descriptions = {'Dashboard': 'A clear view of your stock, value, and next actions.', 'Inventory': 'Find products, keep quantities accurate, and manage your catalogue.',
                        'Movements': 'A permanent audit trail of every stock change.', 'Reports': 'Category performance and items that need attention.', 'Help & About': 'Everything you need to use and demonstrate Stockroom.'}
        self.label(self.content, descriptions[page], color='#607087')
        {'Dashboard': self.dashboard, 'Inventory': self.inventory, 'Movements': self.movements, 'Reports': self.reports, 'Help & About': self.help}[page]()

    def table(self, parent, columns, rows, widths=None):
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True, pady=12)
        tree = ttk.Treeview(frame, columns=columns, show='headings', selectmode='browse')
        tree.tag_configure('even', background='#fafafe')
        tree.tag_configure('low', foreground='#b37623', background='#fffaf0')
        for i, col in enumerate(columns):
            tree.heading(col, text=col, command=lambda c=col: self.sort_tree(tree, c))
            tree.column(col, width=(widths[i] if widths else 130), minwidth=65)
        scroll = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        horizontal = ttk.Scrollbar(frame, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=scroll.set, xscrollcommand=horizontal.set)
        scroll.pack(side='right', fill='y')
        horizontal.pack(side='bottom', fill='x')
        tree.pack(fill='both', expand=True)
        for index, (key, values) in enumerate(rows):
            tree.insert('', 'end', iid=str(key), values=values, tags=('even',) if index % 2 else ())
        return tree

    def sort_tree(self, tree, column):
        reverse = getattr(tree, 'sort_state', None) == (column, False)
        def key(item):
            value = tree.set(item, column)
            try:
                return (0, float(value.replace(',', '').replace('$', '')))
            except ValueError:
                return (1, value.casefold())
        for index, item in enumerate(sorted(tree.get_children(), key=key, reverse=reverse)):
            tree.move(item, '', index)
        tree.sort_state = (column, reverse)

    def panel(self, parent, title, subtitle=None):
        panel = tk.Frame(parent, bg='white', padx=20, pady=16, highlightbackground='#e9e8f1', highlightthickness=1)
        self.label(panel, title, 13, INK, True)
        if subtitle:
            self.label(panel, subtitle, 9, MUTED)
        return panel

    def dashboard(self):
        viewport = tk.Frame(self.content, bg=BG)
        viewport.pack(fill='both', expand=True)
        canvas = tk.Canvas(viewport, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(viewport, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        body = tk.Frame(canvas, bg=BG)
        window = canvas.create_window(0, 0, window=body, anchor='nw')
        body.bind('<Configure>', lambda event: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(window, width=event.width))
        canvas.bind('<MouseWheel>', lambda event: canvas.yview_scroll(-int(event.delta/120), 'units'))
        products = self.store.products()
        low = [p for p in products if p['quantity'] <= p['minimum']]
        cards = tk.Frame(body, bg=BG)
        cards.pack(fill='x', pady=(15, 18))
        metrics = [
            ('Total products', str(len(products)), 'Across your catalogue', BLUE, '▤'),
            ('Units on hand', f"{sum(p['quantity'] for p in products):,}", 'Available in your workspace', '#219b88', '▦'),
            ('Inventory value', f"{sum(p['quantity'] * p['price'] for p in products) / 100:,.2f}", 'At current unit prices', '#4f87d6', '◇'),
            ('Needs attention', str(len(low)), 'At or below minimum stock', '#c38b36', '!')]
        for index, (title, value, note, color, icon) in enumerate(metrics):
            cards.columnconfigure(index, weight=1, uniform='metric')
            card = tk.Frame(cards, bg='white', padx=16, pady=10, highlightbackground='#e9e8f1', highlightthickness=1)
            card.grid(row=0, column=index, sticky='nsew', padx=(0 if index == 0 else 6, 0 if index == 3 else 6))
            tk.Label(card, text=icon, bg='white', fg=color, font=('Segoe UI', 18, 'bold')).pack(side='right', anchor='n')
            self.label(card, title, 10, MUTED).pack_configure(pady=(0, 5))
            self.label(card, value, 23, INK, True).pack_configure(pady=(0, 5))
            self.label(card, note, 8, color).pack_configure(pady=(0, 2))

        middle = tk.Frame(body, bg=BG)
        middle.pack(fill='x', pady=(0, 18))
        middle.columnconfigure(0, weight=3, uniform='middle')
        middle.columnconfigure(1, weight=2, uniform='middle')
        breakdown = self.panel(middle, 'Where your value lives', 'Inventory value by category')
        breakdown.grid(row=0, column=0, sticky='nsew', padx=(0, 9))
        chart = tk.Canvas(breakdown, bg='white', height=145, highlightthickness=0)
        chart.pack(fill='x')
        groups = {}
        for product in products:
            groups[product['category']] = groups.get(product['category'], 0) + product['quantity'] * product['price']
        top = sorted(groups.items(), key=lambda pair: pair[1], reverse=True)[:4]
        def draw_bars(event=None):
            chart.delete('all')
            width = max(chart.winfo_width(), 320)
            maximum = max(groups.values(), default=1) or 1
            colors = (BLUE, '#9c8ff0', '#bdb4f8', '#d9d3fc')
            for i, (category, value) in enumerate(top):
                y = 8 + i * 34
                chart.create_text(0, y+9, text=category[:18], anchor='w', fill='#74768e', font=('Segoe UI', 9))
                start, end = 120, max(145, width-85)
                chart.create_line(start, y+9, end, y+9, fill='#f0eef9', width=11, capstyle='round')
                chart.create_line(start, y+9, start+(end-start)*value/maximum, y+9, fill=colors[i], width=11, capstyle='round')
                chart.create_text(width-2, y+9, text=f'{value/100:,.2f}', anchor='e', fill=INK, font=('Segoe UI', 9, 'bold'))
            if not top:
                chart.create_text(10, 45, text='Add products to see category insights.', anchor='w', fill=MUTED)
        chart.bind('<Configure>', draw_bars)
        health = self.panel(middle, 'Stock health', 'A quick pulse on your inventory')
        health.grid(row=0, column=1, sticky='nsew', padx=(9, 0))
        ring = tk.Canvas(health, bg='white', height=145, highlightthickness=0)
        ring.pack(fill='x')
        def draw_health(event=None):
            ring.delete('all')
            healthy = len(products)-len(low)
            percent = round(100 * healthy/len(products)) if products else 0
            ring.create_oval(6, 7, 122, 123, outline='#f0eef9', width=12)
            if percent:
                ring.create_arc(6, 7, 122, 123, start=90, extent=-359.9*percent/100, style='arc', outline=BLUE, width=12)
            ring.create_text(64, 58, text=f'{percent}%', fill=INK, font=('Segoe UI', 22, 'bold'))
            ring.create_text(64, 83, text='healthy', fill=MUTED, font=('Segoe UI', 9))
            ring.create_text(150, 35, text=f'●  {healthy} well stocked', anchor='w', fill=BLUE, font=('Segoe UI', 10))
            ring.create_text(150, 65, text=f'●  {len(low)} to review', anchor='w', fill='#c38b36', font=('Segoe UI', 10))
            ring.create_text(150, 102, text='Keep your shelves ready.', anchor='w', fill=MUTED, font=('Segoe UI', 9))
        ring.bind('<Configure>', draw_health)

        bottom = tk.Frame(body, bg=BG)
        bottom.pack(fill='both', expand=True)
        watch = self.panel(bottom, 'Reorder watchlist', f'{len(low)} products need a closer look')
        watch.pack(side='left', fill='both', expand=True, padx=(0, 16))
        self.table(watch, ('Product', 'Available', 'Minimum'), [(p['id'], (p['name'], p['quantity'], p['minimum'])) for p in low], [200, 85, 85])
        activity = self.panel(bottom, 'Recent activity', 'Latest stock changes')
        activity.pack(side='right', fill='both')
        for movement in self.store.movements()[:4]:
            row = tk.Frame(activity, bg='white')
            row.pack(fill='x', pady=(5, 9))
            color = '#219b88' if movement['change'] >= 0 else '#c38b36'
            tk.Label(row, text=f"{movement['change']:+d}", width=4, bg='#f1f6f5', fg=color, font=('Segoe UI', 12, 'bold'), pady=6).pack(side='left', padx=(0, 12))
            detail = tk.Frame(row, bg='white')
            detail.pack(side='left')
            tk.Label(detail, text=movement['product_name'][:24], bg='white', fg=INK, font=('Segoe UI', 9, 'bold'), anchor='w').pack(anchor='w')
            tk.Label(detail, text=movement['reason'][:27], bg='white', fg=MUTED, font=('Segoe UI', 8)).pack(anchor='w', pady=(3, 0))
        if not self.store.movements():
            self.label(activity, 'Your stock changes will appear here.', 9, MUTED)

    def inventory(self):
        summary = tk.Frame(self.content, bg=BG)
        summary.pack(fill='x', pady=(12, 8))
        products = self.store.products()
        for text, color in [(f'{len(products)} products', BLUE), (f"{len({p['category'] for p in products})} categories", '#219b88'), (f"{sum(p['quantity'] <= p['minimum'] for p in products)} low stock", '#b88432')]:
            tk.Label(summary, text='  '+text+'  ', bg='white', fg=color, font=('Segoe UI', 10, 'bold'), padx=10, pady=9).pack(side='left', padx=(0, 10))
        toolbar = ttk.Frame(self.content)
        toolbar.pack(fill='x', pady=8)
        self.search = tk.StringVar()
        entry = ttk.Entry(toolbar, textvariable=self.search, width=27)
        entry.pack(side='left', padx=(0, 8))
        self.category = tk.StringVar(value='All categories')
        categories = ['All categories'] + sorted({p['category'] for p in self.store.products()})
        ttk.Combobox(toolbar, textvariable=self.category, values=categories, state='readonly', width=18).pack(side='left', padx=4)
        self.low = tk.BooleanVar()
        ttk.Checkbutton(toolbar, text='Low stock only', variable=self.low, command=self.refresh_inventory).pack(side='left', padx=8)
        ttk.Button(toolbar, text='+ Add product', style='Primary.TButton', command=self.editor).pack(side='right')
        self.label(self.content, 'Search by SKU, name, or category. Click a column heading to sort.', 10, '#607087')
        actions = ttk.Frame(self.content)
        actions.pack(fill='x', pady=(4, 8))
        for text, command in [('Edit', self.edit_selected), ('Adjust stock', self.adjust), ('Delete', self.delete), ('Import CSV', self.import_csv), ('Export CSV', self.export_csv)]:
            ttk.Button(actions, text=text, command=command, style='Danger.TButton' if text == 'Delete' else 'TButton').pack(side='left', padx=(0, 8))
        self.tree = self.table(self.content, ('SKU', 'Product', 'Category', 'Quantity', 'Minimum', 'Unit price', 'Status'), [], [100, 210, 120, 90, 85, 100, 105])
        self.tree.bind('<Double-1>', lambda event: self.edit_selected())
        self.search.trace_add('write', lambda *args: self.refresh_inventory())
        self.category.trace_add('write', lambda *args: self.refresh_inventory())
        self.refresh_inventory()

    def refresh_inventory(self):
        self.tree.delete(*self.tree.get_children())
        query = self.search.get().casefold().strip()
        products = self.store.products()
        for p in products:
            if query not in ' '.join(str(p[k]) for k in ('sku', 'name', 'category')).casefold():
                continue
            if self.category.get() != 'All categories' and p['category'] != self.category.get():
                continue
            if self.low.get() and p['quantity'] > p['minimum']:
                continue
            low = p['quantity'] <= p['minimum']
            status = 'Out of stock' if not p['quantity'] else ('Low stock' if low else 'In stock')
            tags = ('low',) if low else (('even',) if len(self.tree.get_children()) % 2 else ())
            self.tree.insert('', 'end', iid=str(p['id']), values=(p['sku'], p['name'], p['category'], p['quantity'], p['minimum'], f"{p['price']/100:.2f}", status), tags=tags)
        self.status.set(f'{len(self.tree.get_children())} of {len(products)} products • Changes saved automatically')

    def selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo('Select a product', 'Click a product row first.', parent=self)
            return None
        return next((p for p in self.store.products() if p['id'] == int(selection[0])), None)

    def edit_selected(self):
        product = self.selected()
        if product:
            self.editor(product)

    def dialog(self, title):
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.configure(bg=BG, padx=25, pady=22)
        dialog.transient(self)
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.bind('<Escape>', lambda event: dialog.destroy())
        return dialog

    def editor(self, product=None):
        dialog = self.dialog('Edit product' if product else 'Add product')
        self.label(dialog, 'Product details', 20, bold=True)
        variables = {}
        for key, title in zip(COLUMNS, ('SKU (unique)', 'Product name', 'Category', 'Quantity', 'Minimum stock', 'Unit price (e.g. 12.50)')):
            self.label(dialog, title, 10)
            value = product[key] if product else ('0' if key in ('quantity', 'minimum', 'price') else '')
            if product and key == 'price':
                value = f'{value / 100:.2f}'
            variables[key] = tk.StringVar(value=value)
            entry = ttk.Entry(dialog, textvariable=variables[key], width=44)
            entry.pack(fill='x', pady=(0, 10))
            if key == 'sku':
                entry.focus_set()
        def save():
            try:
                self.store.save({k: v.get() for k, v in variables.items()}, product['id'] if product else None)
            except (ValueError, sqlite3.Error) as exc:
                messagebox.showerror('Please check the product', str(exc), parent=dialog)
                return
            dialog.destroy()
            self.show(self.page)
        ttk.Button(dialog, text='Save product', style='Primary.TButton', command=save).pack(fill='x', pady=8)
        ttk.Button(dialog, text='Cancel', command=dialog.destroy).pack(fill='x')

    def adjust(self):
        product = self.selected()
        if not product:
            return
        dialog = self.dialog('Adjust stock')
        self.label(dialog, product['name'], 18, bold=True)
        self.label(dialog, f"Current stock: {product['quantity']}")
        variables = []
        for title in ('Change (+5 received, -2 issued)', 'Reason'):
            self.label(dialog, title)
            variable = tk.StringVar()
            ttk.Entry(dialog, textvariable=variable, width=42).pack(pady=(0, 14))
            variables.append(variable)
        def save():
            try:
                self.store.adjust(product['id'], variables[0].get(), variables[1].get())
            except (ValueError, sqlite3.Error) as exc:
                messagebox.showerror('Check stock adjustment', str(exc), parent=dialog)
                return
            dialog.destroy()
            self.show('Inventory')
        ttk.Button(dialog, text='Save adjustment', command=save, style='Primary.TButton').pack(fill='x')

    def delete(self):
        product = self.selected()
        if product and messagebox.askyesno('Delete product?', f"Delete {product['name']}?\nMovement history will be retained.", parent=self):
            self.store.delete(product['id'])
            self.show('Inventory')

    def import_csv(self):
        path = filedialog.askopenfilename(parent=self, filetypes=[('CSV files', '*.csv')])
        if path:
            try:
                count = self.store.import_csv(path)
                self.show('Inventory')
                messagebox.showinfo('Import complete', f'Imported {count} products.', parent=self)
            except (OSError, ValueError, csv.Error, sqlite3.Error) as exc:
                messagebox.showerror('Import failed', str(exc), parent=self)

    def export_csv(self):
        path = filedialog.asksaveasfilename(parent=self, defaultextension='.csv', initialfile='stockroom-inventory.csv', filetypes=[('CSV files', '*.csv')])
        if path:
            try:
                self.store.export_csv(path)
                self.status.set('Export complete • All inventory products exported')
            except (OSError, UnicodeError) as exc:
                messagebox.showerror('Export failed', str(exc), parent=self)

    def movements(self):
        rows = self.store.movements()
        self.label(self.content, f'{len(rows)} recorded changes • Newest first • History survives product deletion', color='#607087')
        self.table(self.content, ('Date / time', 'Product', 'Change', 'Reason'), [(p['id'], (p['created'].replace('T', ' '), p['product_name'], f"{p['change']:+d}", p['reason'])) for p in rows])

    def reports(self):
        groups = {}
        for p in self.store.products():
            group = groups.setdefault(p['category'], [0, 0, 0, 0])
            group[0] += 1
            group[1] += p['quantity']
            group[2] += p['price'] * p['quantity']
            group[3] += p['quantity'] <= p['minimum']
        self.label(self.content, 'Stock value by category', 16, bold=True)
        chart = tk.Canvas(self.content, height=190, bg='white', highlightthickness=0)
        chart.pack(fill='x', pady=8)
        top = sorted(groups.items(), key=lambda item: item[1][2], reverse=True)[:5]
        maximum = max((v[2] for _, v in top), default=1) or 1
        for i, (name, values) in enumerate(top):
            y = 15 + i * 34
            chart.create_text(14, y+10, text=name[:22], anchor='w', fill=NAV, font=('Segoe UI', 10))
            width = 380 * values[2] / maximum
            chart.create_rectangle(185, y, 185+max(width, 1), y+20, fill=BLUE, outline='')
            chart.create_text(580, y+10, text=f'{values[2]/100:,.2f}', anchor='w', fill=NAV)
        if not top:
            chart.create_text(25, 35, text='Add products to see your category breakdown.', anchor='w', fill=NAV)
        self.table(self.content, ('Category', 'Products', 'Units', 'Stock value', 'Low stock'), [(i, (name, values[0], values[1], f'{values[2]/100:.2f}', values[3])) for i, (name, values) in enumerate(sorted(groups.items()))])
        self.label(self.content, 'Values use your chosen local currency. Low stock means quantity ≤ minimum.', 10, '#607087')

    def help(self):
        sections = [
            ('Getting started', 'Open Inventory → Add product. Enter a unique SKU, a name, category, quantity,\nminimum stock, and unit price. Changes are saved immediately.'),
            ('Everyday workflow', 'Search and filter inventory, then select a row to edit, adjust, or delete it.\nDouble-click a row to edit. Click any column heading to switch sorting direction.'),
            ('Stock and reports', 'Use Adjust stock for deliveries and issues; give each change a reason.\nMovements keeps the history. Reports summarizes units and stock value by category.'),
            ('CSV exchange', 'Export CSV saves the entire inventory. Import CSV adds new products only.\nRequired headers: sku, name, category, quantity, minimum, price.\nDuplicate SKUs or invalid rows cancel the entire import. Prices use a decimal point.'),
            ('Storage and backup', f'Data is stored locally at:\n{self.store.db.execute("PRAGMA database_list").fetchone()[2]}\nClose the app before copying the database as a backup.'),
            ('About Stockroom 1.0', 'Visual Programming project • Python / Tkinter / SQLite\nFive pages, event-driven UI, transactional persistence, reports, and CSV exchange.\nSingle-user application. Amounts have two decimal places and no fixed currency.')]
        frame = ttk.Frame(self.content)
        frame.pack(fill='both', expand=True, pady=12)
        text = tk.Text(frame, wrap='word', bg='white', fg='#43536b', relief='flat',
                       padx=18, pady=18, font=('Segoe UI', 11), cursor='arrow')
        scroll = ttk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        text.pack(fill='both', expand=True)
        text.tag_configure('title', font=('Segoe UI', 13, 'bold'), foreground=NAV, spacing3=8)
        for title, body in sections:
            text.insert('end', title + '\n', 'title')
            text.insert('end', body + '\n\n')
        text.configure(state='disabled')


def main():
    path = Path(os.environ.get('STOCKROOM_DATA_DIR', Path(__file__).resolve().parent.parent / 'data')) / 'stockroom.db'
    try:
        store = Store(path)
    except (OSError, sqlite3.Error) as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror('Cannot open Stockroom', f'Unable to open local storage:\n{exc}')
        root.destroy()
        return
    Application(store).mainloop()
