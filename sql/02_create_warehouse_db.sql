-- ============================================================
-- FILE: 02_create_warehouse_db.sql
-- PURPOSE: Create the Analytics Warehouse Database.
--
-- WHAT IS A DATA WAREHOUSE?
-- The warehouse holds clean, structured, business-ready data.
-- We use a "Star Schema" design:
--   - FACT table: stores measurable events (orders, sales)
--   - DIMENSION tables: store descriptive context (who, what, where, when)
--
-- Star Schema looks like this:
--
--   dim_customers ──┐
--   dim_restaurants─┤
--   dim_food_items ─┼──► fact_orders
--   dim_date ───────┘
--
-- This design makes Power BI queries very fast.
-- ============================================================

CREATE DATABASE IF NOT EXISTS food_order_warehouse;
USE food_order_warehouse;

-- ============================================================
-- DIMENSION TABLE: dim_customers
-- Stores one row per unique customer.
-- We use "SCD Type 1" (overwrite on update) for simplicity.
-- ============================================================
DROP TABLE IF EXISTS dim_customers;

CREATE TABLE dim_customers (
    customer_key    INT AUTO_INCREMENT PRIMARY KEY,  -- surrogate key (warehouse internal ID)
    customer_name   VARCHAR(100) NOT NULL,
    customer_email  VARCHAR(150) NOT NULL UNIQUE,    -- natural key (business identifier)
    customer_phone  VARCHAR(30),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============================================================
-- DIMENSION TABLE: dim_restaurants
-- Stores one row per unique restaurant.
-- ============================================================
DROP TABLE IF EXISTS dim_restaurants;

CREATE TABLE dim_restaurants (
    restaurant_key  INT AUTO_INCREMENT PRIMARY KEY,
    restaurant_name VARCHAR(100) NOT NULL,
    restaurant_city VARCHAR(100) NOT NULL,
    UNIQUE KEY uq_restaurant (restaurant_name, restaurant_city),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============================================================
-- DIMENSION TABLE: dim_food_items
-- Stores one row per unique food item + category combination.
-- ============================================================
DROP TABLE IF EXISTS dim_food_items;

CREATE TABLE dim_food_items (
    food_item_key   INT AUTO_INCREMENT PRIMARY KEY,
    food_item       VARCHAR(100) NOT NULL,
    category        VARCHAR(50) NOT NULL,
    UNIQUE KEY uq_food_item (food_item, category),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- DIMENSION TABLE: dim_date
-- Pre-populated date dimension. Helps Power BI do time
-- intelligence (year-over-year, month comparisons, etc.)
-- ============================================================
DROP TABLE IF EXISTS dim_date;

CREATE TABLE dim_date (
    date_key        INT PRIMARY KEY,         -- format: YYYYMMDD (e.g. 20240105)
    full_date       DATE NOT NULL,
    day_of_week     VARCHAR(10),             -- e.g. Monday
    day_num         TINYINT,                 -- 1=Sunday ... 7=Saturday
    week_num        TINYINT,                 -- week of the year
    month_num       TINYINT,
    month_name      VARCHAR(10),
    quarter_num     TINYINT,
    year_num        SMALLINT,
    is_weekend      TINYINT(1)               -- 1 if Saturday or Sunday
);

-- Populate dim_date for years 2024 and 2025
-- We use a numbers trick to generate one row per day
INSERT INTO dim_date
SELECT
    DATE_FORMAT(d, '%Y%m%d')   AS date_key,
    d                          AS full_date,
    DAYNAME(d)                 AS day_of_week,
    DAYOFWEEK(d)               AS day_num,
    WEEK(d)                    AS week_num,
    MONTH(d)                   AS month_num,
    MONTHNAME(d)               AS month_name,
    QUARTER(d)                 AS quarter_num,
    YEAR(d)                    AS year_num,
    IF(DAYOFWEEK(d) IN (1,7), 1, 0) AS is_weekend
FROM (
    -- Generate a sequence of dates from 2024-01-01 to 2025-12-31
    SELECT DATE_ADD('2024-01-01', INTERVAL seq.n DAY) AS d
    FROM (
        SELECT a.N + b.N * 10 + c.N * 100 + d.N * 1000 AS n
        FROM
            (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3
             UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7
             UNION SELECT 8 UNION SELECT 9) a,
            (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3
             UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7
             UNION SELECT 8 UNION SELECT 9) b,
            (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3
             UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7
             UNION SELECT 8 UNION SELECT 9) c,
            (SELECT 0 AS N UNION SELECT 1) d
    ) seq
    WHERE DATE_ADD('2024-01-01', INTERVAL seq.n DAY) <= '2025-12-31'
) dates;

-- ============================================================
-- FACT TABLE: fact_orders
-- The central table. Each row = one food order.
-- Foreign keys link to all dimension tables.
-- ============================================================
DROP TABLE IF EXISTS fact_orders;

CREATE TABLE fact_orders (
    order_key           INT AUTO_INCREMENT PRIMARY KEY,
    source_order_id     VARCHAR(20) NOT NULL UNIQUE, -- original order_id from source
    customer_key        INT NOT NULL,
    restaurant_key      INT NOT NULL,
    food_item_key       INT NOT NULL,
    order_date_key      INT,           -- FK to dim_date
    delivery_date_key   INT,           -- FK to dim_date (NULL if not delivered)
    quantity            INT NOT NULL,
    unit_price          DECIMAL(10,2) NOT NULL,
    total_amount        DECIMAL(10,2) NOT NULL,
    order_status        VARCHAR(30) NOT NULL,
    payment_method      VARCHAR(50),
    delivery_address    VARCHAR(255),
    driver_name         VARCHAR(100),
    rating              TINYINT,
    load_timestamp      DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- Foreign key constraints ensure data integrity
    FOREIGN KEY (customer_key)    REFERENCES dim_customers(customer_key),
    FOREIGN KEY (restaurant_key)  REFERENCES dim_restaurants(restaurant_key),
    FOREIGN KEY (food_item_key)   REFERENCES dim_food_items(food_item_key),
    FOREIGN KEY (order_date_key)  REFERENCES dim_date(date_key),
    FOREIGN KEY (delivery_date_key) REFERENCES dim_date(date_key)
);

-- Quick check
SHOW TABLES;
