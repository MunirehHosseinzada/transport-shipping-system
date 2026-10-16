import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import re
import datetime

HOST = "localhost"
DATABASES = {
    "vehicles": ["vehicles"],
    "products": ["products"],
    "customers": ["customers", "orders"],
}

def connect():
    return psycopg2.connect(host=HOST, dbname=db_box.get())

def table():
    return table_box.get()

def on_db_change(event=None):
    table_box["values"] = DATABASES[db_box.get()]
    table_box.current(0)
    load_data()

def run_sql(sql, params=()):
    """Run one change (insert/update/delete). Returns True if it worked."""
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return False

VEHICLE_TYPES = ["truck", "van", "cargo ship", "plane"]
VEHICLE_STATUS = ["available", "in transit", "maintenance"]
PRODUCT_CATEGORIES = ["electronics", "furniture", "food", "machinery", "medical", "other"]
PRODUCT_STATUS = ["waiting", "shipped", "delivered"]

PAYMENT_STATUS = ["pending", "paid", "refunded"]

REQUIRED = {
    "vehicles": ["plate_number", "type", "capacity_kg", "driver", "status"],
    "products": ["name", "weight_kg", "category", "destination_city", "status", "customer_id"],
    "customers": ["name", "email", "phone", "city", "address"],
    "orders": ["customer_id", "order_date", "total_price", "payment_status"],
}

CHOICES = {
    "vehicles": {"type": VEHICLE_TYPES, "status": VEHICLE_STATUS},
    "products": {"category": PRODUCT_CATEGORIES, "status": PRODUCT_STATUS},
    "orders": {"payment_status": PAYMENT_STATUS},
}

def lookup_choices(dbname, sql):
    """Returns a list like ['1 - Alice Johnson', ...] from another database."""
    conn = psycopg2.connect(host=HOST, dbname=dbname)
    cur = conn.cursor()
    cur.execute(sql)
    result = [f"{r[0]} - {r[1]}" for r in cur.fetchall()]
    conn.close()
    return result

def get_choices(col):
    t = table()
    if t == "products" and col == "customer_id":
        return lookup_choices("customers", "SELECT id, name FROM customers ORDER BY id")
    if t == "products" and col == "vehicle_id":
        return [""] + lookup_choices("vehicles",
            "SELECT id, plate_number || ' (' || type || ')' FROM vehicles ORDER BY id")
    if t == "orders" and col == "customer_id":
        return lookup_choices("customers", "SELECT id, name FROM customers ORDER BY id")
    return CHOICES.get(t, {}).get(col)

def query_one(dbname, sql, params=()):
    conn = psycopg2.connect(host=HOST, dbname=dbname)
    cur = conn.cursor()
    cur.execute(sql, params)
    result = cur.fetchone()
    conn.close()
    return result

def to_number(text, whole=False):
    try:
        return int(text) if whole else float(text)
    except (TypeError, ValueError):
        return None

def validate(data, row_id):
    """data = dict of field -> text. Returns a list of error messages."""
    errors = []
    t = table()
    other_id = row_id if row_id is not None else -1

    for f in REQUIRED[t]:
        if not data.get(f):
            errors.append(f"{f} is required.")
    if errors:
        return errors

    if t == "vehicles":
        data["plate_number"] = data["plate_number"].upper()
        if not re.fullmatch(r"[A-Z]{3}-\d{3}", data["plate_number"]):
            errors.append("plate_number must look like ABC-123.")
        elif query_one("vehicles",
                "SELECT 1 FROM vehicles WHERE plate_number = %s AND id <> %s",
                (data["plate_number"], other_id)):
            errors.append("This plate number already exists.")
        cap = to_number(data["capacity_kg"], whole=True)
        if cap is None or cap <= 0:
            errors.append("capacity_kg must be a positive whole number.")
        if data["type"].lower() not in VEHICLE_TYPES:
            errors.append("type must be one of: " + ", ".join(VEHICLE_TYPES))
        if data["status"].lower() not in VEHICLE_STATUS:
            errors.append("status must be one of: " + ", ".join(VEHICLE_STATUS))
        data["type"] = data["type"].lower()
        data["status"] = data["status"].lower()

    elif t == "customers":
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", data["email"]):
            errors.append("email is not valid.")
        elif query_one("customers",
                "SELECT 1 FROM customers WHERE email = %s AND id <> %s",
                (data["email"], other_id)):
            errors.append("This email already exists.")
        if not re.fullmatch(r"\+?[0-9\- ]{7,20}", data["phone"]):
            errors.append("phone may only contain digits, +, - and spaces (7-20 chars).")

    elif t == "orders":
        data["payment_status"] = data["payment_status"].lower()
        if data["payment_status"] not in PAYMENT_STATUS:
            errors.append("payment_status must be one of: " + ", ".join(PAYMENT_STATUS))
        price = to_number(data["total_price"])
        if price is None or price <= 0:
            errors.append("total_price must be a positive number.")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data["order_date"]):
            errors.append("order_date must look like 2026-10-16.")
        else:
            try:
                datetime.date.fromisoformat(data["order_date"])
            except ValueError:
                errors.append("order_date is not a real date.")
        cust = to_number(data["customer_id"], whole=True)
        if cust is None or not query_one("customers",
                "SELECT 1 FROM customers WHERE id = %s", (cust,)):
            errors.append("customer_id does not exist in the customers table.")

    elif t == "products":
        data["category"] = data["category"].lower()
        data["status"] = data["status"].lower()
        weight = to_number(data["weight_kg"])
        if weight is None or weight <= 0:
            errors.append("weight_kg must be a positive number.")
        if data["category"] not in PRODUCT_CATEGORIES:
            errors.append("category must be one of: " + ", ".join(PRODUCT_CATEGORIES))
        if data["status"] not in PRODUCT_STATUS:
            errors.append("status must be one of: " + ", ".join(PRODUCT_STATUS))

        cust = to_number(data["customer_id"], whole=True)
        if cust is None or not query_one("customers",
                "SELECT 1 FROM customers WHERE id = %s", (cust,)):
            errors.append("customer_id does not exist in the customers database.")

        veh_text = data.get("vehicle_id")
        if not veh_text:
            if data["status"] in ("shipped", "delivered"):
                errors.append("A shipped/delivered product needs a vehicle_id.")
        else:
            veh = to_number(veh_text, whole=True)
            v = query_one("vehicles",
                    "SELECT capacity_kg, status FROM vehicles WHERE id = %s",
                    (veh,)) if veh is not None else None
            if not v:
                errors.append("vehicle_id does not exist in the vehicles database.")
            else:
                if weight is not None and weight > v[0]:
                    errors.append(f"Product weighs more than the vehicle capacity ({v[0]} kg).")
                if v[1] == "maintenance" and data["status"] == "shipped":
                    errors.append("This vehicle is in maintenance and cannot ship products.")
    return errors

def can_delete(row_id):
    """Block deleting a customer/vehicle that still has products."""
    t = table()
    if t == "customers":
        n_orders = query_one("customers",
            "SELECT COUNT(*) FROM orders WHERE customer_id = %s", (row_id,))[0]
        if n_orders > 0:
            messagebox.showwarning("Cannot delete",
                f"This customer has {n_orders} order(s). Delete them first.")
            return False
        col = "customer_id"
    elif t == "vehicles":
        col = "vehicle_id"
    else:
        return True
    n = query_one("products", f"SELECT COUNT(*) FROM products WHERE {col} = %s", (row_id,))[0]
    if n > 0:
        messagebox.showwarning("Cannot delete",
            f"This row is used by {n} product(s). Reassign or delete them first.")
        return False
    return True

def load_data(event=None):
    conn = connect()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table()} ORDER BY id")
    columns = [d[0] for d in cur.description]
    rows = cur.fetchall()
    conn.close()

    tree.delete(*tree.get_children())
    tree["columns"] = columns
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=110)
    for row in rows:
        tree.insert("", "end", values=row)

def open_form(title, values=None, row_id=None):
    columns = [c for c in tree["columns"] if c != "id"]
    win = tk.Toplevel(root)
    win.title(title)
    win.grab_set()

    entries = {}
    for i, col in enumerate(columns):
        tk.Label(win, text=col).grid(row=i, column=0, padx=10, pady=4, sticky="e")
        choices = get_choices(col)
        current = ""
        if values:
            v = values[i + 1]  # skip id
            current = "" if v == "None" else str(v)
        if choices is not None:
            e = ttk.Combobox(win, values=choices, state="readonly", width=28)
            # for id fields, match the option that starts with the saved id
            match = next((c for c in choices
                          if c == current or c.startswith(current + " - ")), "")
            e.set(match if current else "")
        else:
            e = tk.Entry(win, width=30)
            e.insert(0, current)
        e.grid(row=i, column=1, padx=10, pady=4)
        entries[col] = e

    def save():
        data = {}

        for c in columns:
            text = entries[c].get().strip()
            if c in ("customer_id", "vehicle_id") and text:
                text = text.split(" - ")[0]
            data[c] = text or None
            
        errors = validate(data, row_id)
        if errors:
            messagebox.showerror("Invalid data", "\n".join(errors))
            return
        values_list = [data[c] for c in columns]
        if row_id is None:
            marks = ", ".join(["%s"] * len(columns))
            sql = f"INSERT INTO {table()} ({', '.join(columns)}) VALUES ({marks})"
            ok = run_sql(sql, values_list)
        else:
            sets = ", ".join(f"{c} = %s" for c in columns)
            sql = f"UPDATE {table()} SET {sets} WHERE id = %s"
            ok = run_sql(sql, values_list + [row_id])
        if ok:
            win.destroy()
            load_data()

    tk.Button(win, text="Save", command=save).grid(
        row=len(columns), column=0, columnspan=2, pady=10)

def add_row():
    open_form("Add")

def edit_row():
    sel = tree.selection()
    if not sel:
        messagebox.showinfo("Edit", "Select a row first.")
        return
    values = tree.item(sel[0])["values"]
    open_form("Edit", values=values, row_id=values[0])

def delete_row():
    sel = tree.selection()
    if not sel:
        messagebox.showinfo("Delete", "Select a row first.")
        return
    row_id = tree.item(sel[0])["values"][0]
    if can_delete(row_id) and messagebox.askyesno("Delete", f"Delete row {row_id}?"):
        if run_sql(f"DELETE FROM {table()} WHERE id = %s", (row_id,)):
            load_data()

root = tk.Tk()
root.title("Transport & Shipping System")
root.geometry("900x450")

top = tk.Frame(root)
top.pack(fill="x", padx=10, pady=10)
tk.Label(top, text="Database:").pack(side="left")
db_box = ttk.Combobox(top, values=list(DATABASES), state="readonly")
db_box.pack(side="left", padx=5)
db_box.current(0)
db_box.bind("<<ComboboxSelected>>", on_db_change)

tk.Label(top, text="Table:").pack(side="left", padx=(15, 0))
table_box = ttk.Combobox(top, values=DATABASES["vehicles"], state="readonly")
table_box.pack(side="left", padx=5)
table_box.current(0)
table_box.bind("<<ComboboxSelected>>", load_data)

tree = ttk.Treeview(root, show="headings")
tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

buttons = tk.Frame(root)
buttons.pack(pady=(0, 10))
tk.Button(buttons, text="Add", width=10, command=add_row).pack(side="left", padx=5)
tk.Button(buttons, text="Edit", width=10, command=edit_row).pack(side="left", padx=5)
tk.Button(buttons, text="Delete", width=10, command=delete_row).pack(side="left", padx=5)

load_data()
root.mainloop()