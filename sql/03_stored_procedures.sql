-- ============================================================
-- FILE: 03_stored_procedures.sql
-- PURPOSE: Stored procedures to transform data from
--          staging → warehouse (the "T" in ETL).
--
-- WHAT IS A STORED PROCEDURE?
-- A stored procedure is a saved block of SQL that you can
-- call by name instead of writing the same SQL repeatedly.
-- Think of it like a function in programming.
-- Real companies use stored procedures because:
--   1. Logic lives in the database (not scattered in scripts)
--   2. Faster execution (MySQL compiles them)
--   3. Easy to re-run or schedule
-- ============================================================

USE food_order_staging;

-- MySQL requires changing the delimiter when defining procedures
-- because procedures contain semicolons internally
DELIMITER $$

-- ============================================================
-- PROCEDURE: sp_load_dim_customers
-- Reads unprocessed rows from stg_orders and inserts/updates
-- the dim_customers dimension table.
-- Uses INSERT ... ON DUPLICATE KEY UPDATE (called an "upsert"):
--   - If customer email is new → INSERT
--   - If customer email exists → UPDATE name/phone
-- ============================================================
DROP PROCEDURE IF EXISTS sp_load_dim_customers$$

CREATE PROCEDURE sp_load_dim_customers()
BEGIN
    DECLARE rows_affected INT DEFAULT 0;

    INSERT INTO food_order_warehouse.dim_customers
        (customer_name, customer_email, customer_phone)
    SELECT DISTINCT
        TRIM(customer_name),
        LOWER(TRIM(customer_email)),   -- normalize email to lowercase
        TRIM(customer_phone)
    FROM food_order_staging.stg_orders
    WHERE is_processed = 0
      AND customer_email IS NOT NULL
      AND customer_email != ''
    ON DUPLICATE KEY UPDATE
        customer_name  = VALUES(customer_name),
        customer_phone = VALUES(customer_phone),
        updated_at     = CURRENT_TIMESTAMP;

    SET rows_affected = ROW_COUNT();
    SELECT CONCAT('dim_customers: ', rows_affected, ' rows inserted/updated') AS result;
END$$

-- ============================================================
-- PROCEDURE: sp_load_dim_restaurants
-- ============================================================
DROP PROCEDURE IF EXISTS sp_load_dim_restaurants$$

CREATE PROCEDURE sp_load_dim_restaurants()
BEGIN
    INSERT INTO food_order_warehouse.dim_restaurants
        (restaurant_name, restaurant_city)
    SELECT DISTINCT
        TRIM(restaurant_name),
        TRIM(restaurant_city)
    FROM food_order_staging.stg_orders
    WHERE is_processed = 0
      AND restaurant_name IS NOT NULL
    ON DUPLICATE KEY UPDATE
        updated_at = CURRENT_TIMESTAMP;

    SELECT CONCAT('dim_restaurants: ', ROW_COUNT(), ' rows inserted/updated') AS result;
END$$

-- ============================================================
-- PROCEDURE: sp_load_dim_food_items
-- ============================================================
DROP PROCEDURE IF EXISTS sp_load_dim_food_items$$

CREATE PROCEDURE sp_load_dim_food_items()
BEGIN
    INSERT INTO food_order_warehouse.dim_food_items
        (food_item, category)
    SELECT DISTINCT
        TRIM(food_item),
        TRIM(category)
    FROM food_order_staging.stg_orders
    WHERE is_processed = 0
      AND food_item IS NOT NULL
    ON DUPLICATE KEY UPDATE
        food_item = VALUES(food_item);  -- no-op update to avoid error

    SELECT CONCAT('dim_food_items: ', ROW_COUNT(), ' rows inserted/updated') AS result;
END$$

-- ============================================================
-- PROCEDURE: sp_load_fact_orders
-- The main transformation. Joins staging data with all
-- dimension tables to build the fact table.
-- Skips orders already loaded (uses source_order_id as guard).
-- Also handles NULLs and type casting here.
-- ============================================================
DROP PROCEDURE IF EXISTS sp_load_fact_orders$$

CREATE PROCEDURE sp_load_fact_orders()
BEGIN
    DECLARE rows_inserted INT DEFAULT 0;

    INSERT INTO food_order_warehouse.fact_orders (
        source_order_id,
        customer_key,
        restaurant_key,
        food_item_key,
        order_date_key,
        delivery_date_key,
        quantity,
        unit_price,
        total_amount,
        order_status,
        payment_method,
        delivery_address,
        driver_name,
        rating
    )
    SELECT
        s.order_id,
        c.customer_key,
        r.restaurant_key,
        f.food_item_key,
        -- Convert order_date string to date_key integer (YYYYMMDD)
        CAST(DATE_FORMAT(STR_TO_DATE(s.order_date, '%Y-%m-%d %H:%i:%s'), '%Y%m%d') AS UNSIGNED),
        -- delivery_date can be NULL (e.g. for cancelled orders)
        CASE
            WHEN s.delivery_date IS NOT NULL AND s.delivery_date != ''
            THEN CAST(DATE_FORMAT(STR_TO_DATE(s.delivery_date, '%Y-%m-%d %H:%i:%s'), '%Y%m%d') AS UNSIGNED)
            ELSE NULL
        END,
        CAST(s.quantity AS UNSIGNED),
        CAST(s.unit_price AS DECIMAL(10,2)),
        CAST(s.total_amount AS DECIMAL(10,2)),
        TRIM(s.order_status),
        TRIM(s.payment_method),
        TRIM(s.delivery_address),
        NULLIF(TRIM(s.driver_name), ''),  -- store NULL instead of empty string
        CASE
            WHEN s.rating IS NOT NULL AND s.rating != ''
            THEN CAST(s.rating AS UNSIGNED)
            ELSE NULL
        END
    FROM food_order_staging.stg_orders s
    -- Join to dimension tables to get surrogate keys
    JOIN food_order_warehouse.dim_customers c
        ON LOWER(TRIM(s.customer_email)) = c.customer_email
    JOIN food_order_warehouse.dim_restaurants r
        ON TRIM(s.restaurant_name) = r.restaurant_name
        AND TRIM(s.restaurant_city) = r.restaurant_city
    JOIN food_order_warehouse.dim_food_items f
        ON TRIM(s.food_item) = f.food_item
        AND TRIM(s.category) = f.category
    WHERE s.is_processed = 0
      AND s.order_id IS NOT NULL
    -- Skip orders that are already in the warehouse (idempotent)
    ON DUPLICATE KEY UPDATE
        order_status = VALUES(order_status),
        delivery_date_key = VALUES(delivery_date_key),
        driver_name  = VALUES(driver_name),
        rating       = VALUES(rating),
        load_timestamp = CURRENT_TIMESTAMP;

    SET rows_inserted = ROW_COUNT();
    SELECT CONCAT('fact_orders: ', rows_inserted, ' rows inserted/updated') AS result;
END$$

-- ============================================================
-- PROCEDURE: sp_mark_staging_processed
-- After all warehouse loads succeed, mark staging rows as
-- processed so they won't be loaded again.
-- ============================================================
DROP PROCEDURE IF EXISTS sp_mark_staging_processed$$

CREATE PROCEDURE sp_mark_staging_processed()
BEGIN
    UPDATE food_order_staging.stg_orders
    SET is_processed = 1
    WHERE is_processed = 0;

    SELECT CONCAT('Marked ', ROW_COUNT(), ' staging rows as processed') AS result;
END$$

-- ============================================================
-- PROCEDURE: sp_run_full_etl
-- MASTER PROCEDURE: calls all the above in the right order.
-- This is what the Python pipeline calls with a single command.
-- Order matters: dimensions must be loaded BEFORE the fact table
-- because fact_orders has foreign keys pointing to them.
-- ============================================================
DROP PROCEDURE IF EXISTS sp_run_full_etl$$

CREATE PROCEDURE sp_run_full_etl()
BEGIN
    DECLARE exit handler FOR SQLEXCEPTION
    BEGIN
        -- If anything fails, roll back and log the error
        ROLLBACK;
        INSERT INTO food_order_staging.etl_job_log
            (job_name, status, start_time, end_time, error_message)
        VALUES
            ('sp_run_full_etl', 'FAILED', NOW(), NOW(), 'SQL Exception occurred during ETL');
        SELECT 'ETL FAILED - check etl_job_log for details' AS result;
    END;

    START TRANSACTION;

    -- Log job start
    INSERT INTO food_order_staging.etl_job_log
        (job_name, status, start_time)
    VALUES ('sp_run_full_etl', 'STARTED', NOW());

    -- Step 1: Load dimension tables (order doesn't matter between dims)
    CALL sp_load_dim_customers();
    CALL sp_load_dim_restaurants();
    CALL sp_load_dim_food_items();

    -- Step 2: Load fact table (must come after dimensions)
    CALL sp_load_fact_orders();

    -- Step 3: Mark staging rows as processed
    CALL sp_mark_staging_processed();

    COMMIT;

    -- Log job success
    UPDATE food_order_staging.etl_job_log
    SET status = 'SUCCESS', end_time = NOW()
    WHERE job_id = LAST_INSERT_ID();

    SELECT 'ETL completed successfully!' AS result;
END$$

DELIMITER ;

-- ============================================================
-- Quick test: verify procedures were created
-- ============================================================
SHOW PROCEDURE STATUS WHERE Db IN ('food_order_staging', 'food_order_warehouse');
