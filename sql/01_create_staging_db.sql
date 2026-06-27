-- ============================================================
-- FILE: 01_create_staging_db.sql
-- PURPOSE: Create the Staging Database and its tables.
--
-- WHAT IS A STAGING DATABASE?
-- Think of staging as a "loading dock" for your data.
-- Raw data from the source (CSV / website) lands here first,
-- exactly as it arrived — no transformations yet.
-- This protects your clean warehouse from bad data, and lets
-- you re-run transformations without re-fetching source data.
-- ============================================================

-- Step 1: Create the staging database (run this once)
CREATE DATABASE IF NOT EXISTS food_order_staging;
USE food_order_staging;

-- ============================================================
-- TABLE: stg_orders
-- This mirrors the structure of the raw CSV file.
-- All columns are VARCHAR/TEXT so we accept data as-is,
-- even if it has formatting issues. Cleaning happens later.
-- ============================================================
DROP TABLE IF EXISTS stg_orders;

CREATE TABLE stg_orders (
    stg_id          INT AUTO_INCREMENT PRIMARY KEY,  -- internal staging row ID
    order_id        VARCHAR(20),
    customer_name   VARCHAR(100),
    customer_email  VARCHAR(150),
    customer_phone  VARCHAR(30),
    restaurant_name VARCHAR(100),
    restaurant_city VARCHAR(100),
    food_item       VARCHAR(100),
    category        VARCHAR(50),
    quantity        VARCHAR(10),    -- stored as string; we cast to INT in the warehouse
    unit_price      VARCHAR(20),    -- stored as string; we cast to DECIMAL in the warehouse
    total_amount    VARCHAR(20),
    order_date      VARCHAR(30),    -- stored as string; we cast to DATETIME in the warehouse
    delivery_date   VARCHAR(30),
    order_status    VARCHAR(30),
    payment_method  VARCHAR(50),
    delivery_address VARCHAR(255),
    driver_name     VARCHAR(100),
    rating          VARCHAR(5),
    -- ETL metadata columns (added by our pipeline, not in the source CSV)
    load_timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP,  -- when this row was loaded
    source_file     VARCHAR(255),                         -- which file this row came from
    is_processed    TINYINT(1) DEFAULT 0                  -- 0 = not yet moved to warehouse
);

-- ============================================================
-- TABLE: etl_job_log
-- Tracks every time the ETL pipeline runs.
-- This is critical for debugging — if something breaks,
-- you can see exactly which job failed and why.
-- ============================================================
DROP TABLE IF EXISTS etl_job_log;

CREATE TABLE etl_job_log (
    job_id          INT AUTO_INCREMENT PRIMARY KEY,
    job_name        VARCHAR(100) NOT NULL,        -- e.g. "load_staging", "transform_warehouse"
    status          ENUM('STARTED', 'SUCCESS', 'FAILED') NOT NULL,
    rows_processed  INT DEFAULT 0,                -- how many rows were handled
    start_time      DATETIME NOT NULL,
    end_time        DATETIME,
    error_message   TEXT,                         -- stores error details if status = FAILED
    source_file     VARCHAR(255)
);

-- Quick check: show the tables we just created
SHOW TABLES;
