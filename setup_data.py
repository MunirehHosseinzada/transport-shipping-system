import psycopg2

HOST = "localhost"

def create_db(name):
    conn = psycopg2.connect(host=HOST, dbname="postgres")
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
    if cur.fetchone():
        print(f"Database '{name}' already exists, skipping.")
    else:
        cur.execute(f"CREATE DATABASE {name}")
        print(f"Database '{name}' created.")
    conn.close()

def run(dbname, sql):
    conn = psycopg2.connect(host=HOST, dbname=dbname)
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    conn.close()

for name in ["vehicles", "products", "customers"]:
    create_db(name)

run("vehicles", """
CREATE TABLE IF NOT EXISTS vehicles (
    id SERIAL PRIMARY KEY,
    plate_number TEXT,
    type TEXT,
    capacity_kg INTEGER,
    driver TEXT,
    status TEXT
)""")

run("products", """
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT,
    weight_kg NUMERIC,
    category TEXT,
    destination_city TEXT,
    status TEXT,
    customer_id INTEGER,
    vehicle_id INTEGER
)""")

run("customers", """
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name TEXT,
    email TEXT,
    phone TEXT,
    city TEXT,
    address TEXT
)""")

run("customers", """
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    order_date DATE,
    total_price NUMERIC,
    payment_status TEXT
)""")

print("Setup finished.")

def fill(dbname, table, columns, rows):
    conn = psycopg2.connect(host=HOST, dbname=dbname)
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    if cur.fetchone()[0] > 0:
        print(f"Table '{table}' already has data, skipping.")
    else:
        placeholders = ", ".join(["%s"] * len(columns))
        cols = ", ".join(columns)
        cur.executemany(
            f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", rows
        )
        conn.commit()
        print(f"Inserted {len(rows)} rows into '{table}'.")
    conn.close()

fill("vehicles", "vehicles",
    ["plate_number", "type", "capacity_kg", "driver", "status"], [
    ("TRK-101", "truck", 12000, "John Miller", "in transit"),
    ("TRK-102", "truck", 15000, "Sara Lopez", "available"),
    ("TRK-103", "truck", 10000, "Ahmed Khan", "maintenance"),
    ("VAN-201", "van", 1500, "Emily Chen", "in transit"),
    ("VAN-202", "van", 1800, "David Brown", "available"),
    ("VAN-203", "van", 2000, "Olga Petrova", "in transit"),
    ("SHP-301", "cargo ship", 500000, "Captain Rossi", "in transit"),
    ("SHP-302", "cargo ship", 750000, "Captain Nilsson", "available"),
    ("PLN-401", "plane", 40000, "Pilot Garcia", "available"),
    ("PLN-402", "plane", 55000, "Pilot Tanaka", "maintenance"),
])

fill("customers", "customers",
    ["name", "email", "phone", "city", "address"], [
    ("Alice Johnson", "alice@example.com", "+1-555-0101", "New York", "12 Broadway St"),
    ("Bob Smith", "bob@example.com", "+1-555-0102", "Chicago", "45 Lake Ave"),
    ("Carla Gomez", "carla@example.com", "+34-555-0103", "Madrid", "7 Calle Mayor"),
    ("Dmitri Ivanov", "dmitri@example.com", "+7-555-0104", "Moscow", "22 Tverskaya St"),
    ("Emma Wilson", "emma@example.com", "+44-555-0105", "London", "9 Baker Street"),
    ("Farid Rahimi", "farid@example.com", "+49-555-0106", "Berlin", "31 Berliner Str"),
    ("Grace Kim", "grace@example.com", "+82-555-0107", "Seoul", "88 Gangnam-daero"),
    ("Hiro Sato", "hiro@example.com", "+81-555-0108", "Tokyo", "5 Shibuya Ave"),
    ("Isabel Costa", "isabel@example.com", "+351-555-0109", "Lisbon", "14 Rua Augusta"),
    ("Jack Taylor", "jack@example.com", "+61-555-0110", "Sydney", "60 George St"),
])

fill("products", "products",
    ["name", "weight_kg", "category", "destination_city", "status", "customer_id", "vehicle_id"], [
    ("Laptops (box of 20)", 60, "electronics", "New York", "shipped", 1, 4),
    ("Office desks", 450, "furniture", "Chicago", "shipped", 2, 1),
    ("Frozen fish", 2000, "food", "Madrid", "waiting", 3, 2),
    ("Wooden chairs", 300, "furniture", "Moscow", "waiting", 4, 5),
    ("Smartphones (box of 50)", 40, "electronics", "London", "shipped", 5, 9),
    ("Auto parts", 8000, "machinery", "Berlin", "delivered", 6, 2),
    ("Rice sacks", 12000, "food", "Seoul", "shipped", 7, 7),
    ("Televisions", 700, "electronics", "Tokyo", "shipped", 8, 6),
    ("Olive oil barrels", 1500, "food", "Lisbon", "delivered", 9, 5),
    ("Solar panels", 3500, "electronics", "Sydney", "waiting", 10, 8),
    ("Sofa set", 250, "furniture", "New York", "delivered", 1, 4),
    ("Medical supplies", 900, "medical", "London", "shipped", 5, 9),
    ("Construction tools", 2200, "machinery", "Chicago", "waiting", 2, 1),
    ("Books (pallet)", 600, "other", "Berlin", "delivered", 6, 5),
    ("Bicycles", 800, "other", "Tokyo", "waiting", 8, 6),
])

fill("customers", "orders",
    ["customer_id", "order_date", "total_price", "payment_status"], [
    (1, "2026-08-02", 4500.00, "paid"),
    (1, "2026-09-10", 1200.50, "pending"),
    (2, "2026-08-15", 3100.00, "paid"),
    (3, "2026-09-01", 2750.00, "pending"),
    (4, "2026-09-12", 980.00, "paid"),
    (5, "2026-07-20", 5600.00, "paid"),
    (5, "2026-09-25", 1900.00, "refunded"),
    (6, "2026-08-30", 7200.00, "paid"),
    (7, "2026-09-05", 12500.00, "pending"),
    (8, "2026-10-01", 2300.00, "paid"),
    (9, "2026-09-18", 1600.00, "paid"),
    (10, "2026-10-08", 4100.00, "pending"),
])