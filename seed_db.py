import os
import psycopg2
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

schema_sql = """
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS products CASCADE;

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    signup_date DATE NOT NULL
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10,2) NOT NULL
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    product_id INT REFERENCES products(product_id),
    order_date DATE NOT NULL,
    gross_amount DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0.00,
    net_amount DECIMAL(10,2) NOT NULL,
    order_status VARCHAR(20) DEFAULT 'completed'
);

-- Seed Data
INSERT INTO customers (name, email, status, signup_date) VALUES
('Alice Smith', 'alice@example.com', 'vip', '2025-01-15'),
('Bob Jones', 'bob@example.com', 'active', '2025-03-22'),
('Charlie Brown', 'charlie@example.com', 'inactive', '2025-05-10');

INSERT INTO products (product_name, category, price) VALUES
('Enterprise License', 'Software', 1500.00),
('Cloud Hosting', 'Services', 300.00),
('Consulting Hour', 'Services', 150.00);

INSERT INTO orders (customer_id, product_id, order_date, gross_amount, discount_amount, net_amount, order_status) VALUES
(1, 1, '2026-01-10', 1500.00, 100.00, 1400.00, 'completed'),
(1, 2, '2026-02-14', 300.00, 0.00, 300.00, 'completed'),
(2, 3, '2026-03-01', 150.00, 0.00, 150.00, 'returned'),
(3, 2, '2026-03-05', 300.00, 50.00, 250.00, 'completed');
"""

def seed():
    # Connect to PostgreSQL using the URL from .env
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute(schema_sql)
    conn.commit()
    cur.close()
    conn.close()
    print("Database successfully seeded.")

if __name__ == "__main__":
    seed()