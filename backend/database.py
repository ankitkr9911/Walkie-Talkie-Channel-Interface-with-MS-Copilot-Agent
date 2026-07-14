"""
database.py — SQLite Database Layer
====================================
Handles schema creation, seed data, and query execution.
Uses aiosqlite for async compatibility with FastAPI.

Migration to PostgreSQL: swap aiosqlite → asyncpg, change ? → $1 placeholders,
and update the connection string. No schema changes needed.
"""

import aiosqlite
import os

# ---------- Configuration ----------
DB_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "inventory.db"))


# ---------- Query Helpers ----------
async def execute_query(query: str, params: tuple = ()) -> list[dict]:
    """Execute a SELECT query and return results as list of dicts."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def execute_scalar(query: str, params: tuple = ()):
    """Execute a query and return a single scalar value."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


# ---------- Schema Initialization ----------
async def init_db():
    """Create all tables if they don't exist, then seed with sample data."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        await db.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            );

            CREATE TABLE IF NOT EXISTS warehouses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT,
                city TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_email TEXT,
                phone TEXT
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category_id INTEGER REFERENCES categories(id),
                supplier_id INTEGER REFERENCES suppliers(id),
                unit_price REAL NOT NULL,
                sku TEXT UNIQUE NOT NULL,
                description TEXT
            );

            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER REFERENCES products(id),
                warehouse_id INTEGER REFERENCES warehouses(id),
                quantity INTEGER NOT NULL DEFAULT 0,
                reorder_level INTEGER NOT NULL DEFAULT 10,
                last_restocked TEXT
            );
        """)
        await db.commit()

    # Seed only if tables are empty
    count = await execute_scalar("SELECT COUNT(*) FROM categories")
    if count == 0:
        await _seed_db()


# ---------- Seed Data ----------
async def _seed_db():
    """Populate database with realistic IT inventory data for demo/testing."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        # -- Categories --
        await db.executemany(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            [
                ("Laptops", "Portable computing devices"),
                ("Monitors", "Display screens and panels"),
                ("Desktops", "Desktop computers and workstations"),
                ("Accessories", "Peripherals, docks, webcams, and accessories"),
                ("Networking", "Switches, routers, and network equipment"),
            ],
        )

        # -- Warehouses (4 major Indian cities) --
        await db.executemany(
            "INSERT INTO warehouses (name, location, city) VALUES (?, ?, ?)",
            [
                ("Bangalore Central Warehouse", "Whitefield Tech Park, Phase 2", "Bangalore"),
                ("Mumbai Main Depot", "Andheri East Industrial Area", "Mumbai"),
                ("Delhi North Hub", "Sector 62, Noida", "Delhi"),
                ("Hyderabad Tech Center", "HITEC City, Madhapur", "Hyderabad"),
            ],
        )

        # -- Suppliers --
        await db.executemany(
            "INSERT INTO suppliers (name, contact_email, phone) VALUES (?, ?, ?)",
            [
                ("Dell Technologies", "enterprise@dell.com", "+91-80-4567-8901"),
                ("HP Inc", "orders@hp.com", "+91-22-3456-7890"),
                ("Lenovo Group", "sales@lenovo.com", "+91-11-2345-6789"),
                ("Logitech International", "business@logitech.com", "+91-40-1234-5678"),
                ("Cisco Systems", "procurement@cisco.com", "+91-80-9876-5432"),
            ],
        )

        # -- Products (20 realistic IT products) --
        products = [
            # Laptops (category_id=1)
            ("Dell Latitude 5440", 1, 1, 72000, "DELL-LAT-5440", "14-inch business laptop, i5, 16GB RAM, 512GB SSD"),
            ("Dell Latitude 7440", 1, 1, 95000, "DELL-LAT-7440", "14-inch premium ultrabook, i7, 16GB RAM, 1TB SSD"),
            ("Dell Inspiron 15", 1, 1, 55000, "DELL-INS-15", "15.6-inch consumer laptop, i5, 8GB RAM, 256GB SSD"),
            ("HP EliteBook 840 G10", 1, 2, 85000, "HP-EB-840G10", "14-inch business laptop, i7, 16GB RAM, 512GB SSD"),
            ("HP ProBook 450 G10", 1, 2, 62000, "HP-PB-450G10", "15.6-inch business laptop, i5, 8GB RAM, 512GB SSD"),
            ("Lenovo ThinkPad X1 Carbon", 1, 3, 110000, "LEN-TP-X1C", "14-inch ultrabook, i7, 16GB RAM, 1TB SSD"),
            ("Lenovo IdeaPad Slim 5", 1, 3, 58000, "LEN-IP-SLIM5", "15.6-inch laptop, Ryzen 5, 8GB RAM, 512GB SSD"),
            # Monitors (category_id=2)
            ("Dell UltraSharp U2723QE", 2, 1, 48000, "DELL-MON-U2723", "27-inch 4K USB-C Hub Monitor"),
            ("HP E24 G5 Monitor", 2, 2, 15000, "HP-MON-E24G5", "23.8-inch FHD IPS Monitor"),
            ("Lenovo ThinkVision T24i-30", 2, 3, 14500, "LEN-MON-T24I", "23.8-inch FHD Monitor with USB-C"),
            ("Dell P2422H Monitor", 2, 1, 18500, "DELL-MON-P2422", "24-inch FHD IPS Monitor"),
            # Desktops (category_id=3)
            ("Dell OptiPlex 7010", 3, 1, 65000, "DELL-OPT-7010", "Small form factor desktop, i5, 16GB, 512GB SSD"),
            ("HP ProDesk 400 G9", 3, 2, 52000, "HP-PD-400G9", "Micro tower desktop, i5, 8GB, 256GB SSD"),
            ("Lenovo ThinkCentre M70q", 3, 3, 48000, "LEN-TC-M70Q", "Tiny desktop, i5, 8GB, 256GB SSD"),
            # Accessories (category_id=4)
            ("Logitech MX Master 3S", 4, 4, 8500, "LOG-MX-MSTR3S", "Wireless ergonomic mouse, Bluetooth/USB-C"),
            ("Logitech MX Keys S", 4, 4, 7200, "LOG-MX-KEYS-S", "Wireless keyboard with smart backlighting"),
            ("Dell WB7022 Webcam", 4, 1, 12000, "DELL-WB-7022", "4K Ultra HD webcam with AI auto-framing"),
            ("HP USB-C Dock G5", 4, 2, 18500, "HP-DOCK-G5", "USB-C universal docking station"),
            # Networking (category_id=5)
            ("Cisco Catalyst 1000-24T", 5, 5, 35000, "CISCO-CAT-1000", "24-port Gigabit managed switch"),
            ("Logitech Rally Bar", 4, 4, 245000, "LOG-RALLY-BAR", "All-in-one video conferencing bar"),
        ]
        await db.executemany(
            "INSERT INTO products (name, category_id, supplier_id, unit_price, sku, description) VALUES (?, ?, ?, ?, ?, ?)",
            products,
        )

        # -- Inventory (distributed across warehouses, includes low/zero stock items) --
        inventory = [
            # Dell Latitude 5440 — well stocked everywhere
            (1, 1, 45, 10, "2024-06-15"),  (1, 2, 30, 10, "2024-06-10"),
            (1, 3, 22, 10, "2024-05-28"),  (1, 4, 38, 10, "2024-06-20"),
            # Dell Latitude 7440 — limited
            (2, 1, 12, 8, "2024-06-01"),   (2, 2, 5, 8, "2024-05-15"),
            (2, 4, 8, 8, "2024-06-05"),
            # Dell Inspiron 15
            (3, 1, 60, 15, "2024-06-18"),  (3, 3, 40, 15, "2024-06-12"),
            # HP EliteBook 840 G10
            (4, 1, 25, 10, "2024-06-08"),  (4, 2, 18, 10, "2024-05-30"),
            (4, 4, 20, 10, "2024-06-14"),
            # HP ProBook 450 G10
            (5, 2, 35, 12, "2024-06-16"),  (5, 3, 28, 12, "2024-06-11"),
            # Lenovo ThinkPad X1 Carbon — premium, very low stock
            (6, 1, 8, 5, "2024-06-03"),    (6, 4, 3, 5, "2024-05-20"),
            # Lenovo IdeaPad Slim 5
            (7, 2, 42, 15, "2024-06-19"),  (7, 3, 30, 15, "2024-06-13"),
            # Dell UltraSharp Monitor
            (8, 1, 15, 5, "2024-06-07"),   (8, 2, 10, 5, "2024-05-25"),
            # HP E24 G5 Monitor — high stock everywhere
            (9, 1, 50, 20, "2024-06-17"),  (9, 2, 45, 20, "2024-06-15"),
            (9, 3, 35, 20, "2024-06-10"),  (9, 4, 40, 20, "2024-06-12"),
            # Lenovo ThinkVision
            (10, 1, 30, 15, "2024-06-14"), (10, 3, 25, 15, "2024-06-09"),
            # Dell P2422H — OUT OF STOCK in Hyderabad
            (11, 2, 55, 20, "2024-06-20"), (11, 4, 0, 20, "2024-04-01"),
            # Dell OptiPlex 7010
            (12, 1, 20, 8, "2024-06-06"),  (12, 3, 15, 8, "2024-05-28"),
            # HP ProDesk 400 G9
            (13, 2, 18, 10, "2024-06-10"), (13, 4, 12, 10, "2024-06-05"),
            # Lenovo ThinkCentre M70q — OUT OF STOCK in Delhi
            (14, 1, 25, 10, "2024-06-15"), (14, 3, 0, 10, "2024-03-15"),
            # Logitech MX Master 3S — very high stock
            (15, 1, 100, 30, "2024-06-20"), (15, 2, 85, 30, "2024-06-18"),
            (15, 3, 70, 30, "2024-06-15"),  (15, 4, 90, 30, "2024-06-19"),
            # Logitech MX Keys S
            (16, 1, 80, 25, "2024-06-19"), (16, 2, 65, 25, "2024-06-16"),
            # Dell WB7022 Webcam — very low in Hyderabad
            (17, 1, 40, 15, "2024-06-12"), (17, 4, 2, 15, "2024-05-01"),
            # HP USB-C Dock G5
            (18, 1, 30, 10, "2024-06-14"), (18, 2, 25, 10, "2024-06-11"),
            # Cisco Catalyst Switch
            (19, 1, 10, 5, "2024-06-05"),  (19, 3, 7, 5, "2024-05-22"),
            # Logitech Rally Bar — premium, very limited
            (20, 1, 3, 2, "2024-05-10"),   (20, 4, 1, 2, "2024-04-15"),
        ]
        await db.executemany(
            "INSERT INTO inventory (product_id, warehouse_id, quantity, reorder_level, last_restocked) VALUES (?, ?, ?, ?, ?)",
            inventory,
        )

        await db.commit()
        print(f"[OK] Database seeded: {len(products)} products, {len(inventory)} inventory records across 4 warehouses")
