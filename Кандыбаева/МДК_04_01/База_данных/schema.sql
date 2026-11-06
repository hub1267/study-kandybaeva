PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS manufacturers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    manufacturer_id INTEGER NOT NULL REFERENCES manufacturers(id),
    price NUMERIC NOT NULL CHECK (price >= 0),
    image TEXT,
    UNIQUE (name, manufacturer_id)
);
CREATE TABLE IF NOT EXISTS sizes (
    id INTEGER PRIMARY KEY,
    size INTEGER NOT NULL UNIQUE CHECK (size > 0)
);
CREATE TABLE IF NOT EXISTS stock (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    size_id INTEGER NOT NULL REFERENCES sizes(id),
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    UNIQUE (product_id, size_id)
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    login TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL CHECK (role IN ('Покупатель', 'Менеджер', 'Администратор'))
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    order_date TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    size_id INTEGER NOT NULL REFERENCES sizes(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC NOT NULL CHECK (unit_price >= 0)
);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_stock_product ON stock(product_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
