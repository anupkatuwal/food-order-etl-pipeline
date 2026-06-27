-- ============================================================
-- FILE: 04_sample_queries.sql
-- PURPOSE: Business analytics queries you can run against
--          the warehouse to validate data and generate insights.
--          These are also useful as a basis for Power BI measures.
-- ============================================================

USE food_order_warehouse;

-- ============================================================
-- 1. TOTAL REVENUE BY RESTAURANT
--    Which restaurants are generating the most revenue?
-- ============================================================
SELECT
    r.restaurant_name,
    r.restaurant_city,
    COUNT(f.order_key)             AS total_orders,
    SUM(f.total_amount)            AS total_revenue,
    ROUND(AVG(f.total_amount), 2)  AS avg_order_value
FROM fact_orders f
JOIN dim_restaurants r ON f.restaurant_key = r.restaurant_key
WHERE f.order_status = 'Delivered'
GROUP BY r.restaurant_name, r.restaurant_city
ORDER BY total_revenue DESC;

-- ============================================================
-- 2. REVENUE BY FOOD CATEGORY
--    What categories drive the most sales?
-- ============================================================
SELECT
    fi.category,
    COUNT(f.order_key)            AS total_orders,
    SUM(f.quantity)               AS total_items_sold,
    SUM(f.total_amount)           AS total_revenue,
    ROUND(AVG(f.rating), 2)       AS avg_rating
FROM fact_orders f
JOIN dim_food_items fi ON f.food_item_key = fi.food_item_key
WHERE f.order_status = 'Delivered'
GROUP BY fi.category
ORDER BY total_revenue DESC;

-- ============================================================
-- 3. DAILY ORDER TREND
--    How many orders per day? Useful for spotting peak days.
-- ============================================================
SELECT
    d.full_date,
    d.day_of_week,
    COUNT(f.order_key)    AS total_orders,
    SUM(f.total_amount)   AS daily_revenue
FROM fact_orders f
JOIN dim_date d ON f.order_date_key = d.date_key
GROUP BY d.full_date, d.day_of_week
ORDER BY d.full_date;

-- ============================================================
-- 4. ORDER STATUS BREAKDOWN
--    What % of orders were delivered vs cancelled?
-- ============================================================
SELECT
    order_status,
    COUNT(*)                                          AS order_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS percentage
FROM fact_orders
GROUP BY order_status;

-- ============================================================
-- 5. TOP 5 CUSTOMERS BY SPEND
-- ============================================================
SELECT
    c.customer_name,
    c.customer_email,
    COUNT(f.order_key)    AS total_orders,
    SUM(f.total_amount)   AS total_spent
FROM fact_orders f
JOIN dim_customers c ON f.customer_key = c.customer_key
WHERE f.order_status = 'Delivered'
GROUP BY c.customer_name, c.customer_email
ORDER BY total_spent DESC
LIMIT 5;

-- ============================================================
-- 6. PAYMENT METHOD BREAKDOWN
-- ============================================================
SELECT
    payment_method,
    COUNT(*)                   AS order_count,
    SUM(total_amount)          AS total_revenue
FROM fact_orders
GROUP BY payment_method
ORDER BY order_count DESC;

-- ============================================================
-- 7. DRIVER PERFORMANCE
--    Which drivers get the best ratings?
-- ============================================================
SELECT
    driver_name,
    COUNT(*)               AS deliveries,
    ROUND(AVG(rating), 2)  AS avg_rating,
    MIN(rating)            AS min_rating,
    MAX(rating)            AS max_rating
FROM fact_orders
WHERE driver_name IS NOT NULL
GROUP BY driver_name
ORDER BY avg_rating DESC;

-- ============================================================
-- 8. ETL JOB HISTORY
--    Check the health of your pipeline runs
-- ============================================================
SELECT
    job_id,
    job_name,
    status,
    rows_processed,
    start_time,
    end_time,
    TIMESTAMPDIFF(SECOND, start_time, end_time) AS duration_seconds,
    error_message
FROM food_order_staging.etl_job_log
ORDER BY job_id DESC;
