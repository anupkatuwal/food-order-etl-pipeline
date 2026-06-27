# ============================================================
# FILE: load_staging.py
# PURPOSE: Load raw extracted data into the staging database.
#          This is the "L" (Load) part of ETL — loading into staging.
#
# WHY LOAD TO STAGING FIRST?
# We load data as-is into staging before any transformation.
# Benefits:
#   1. If transformation fails, raw data is still safely stored
#   2. You can re-run transformations without re-fetching source
#   3. You have an audit trail of what data came in
# ============================================================

import mysql.connector
import logging
from datetime import datetime
from config import DB_CONFIG, STAGING_DB, RAW_CSV_FILE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def get_connection(database=None):
    """
    Creates and returns a MySQL connection.
    'database' param is optional — we may connect without
    selecting a DB first (e.g. to check if DB exists).
    """
    cfg = DB_CONFIG.copy()
    if database:
        cfg["database"] = database
    return mysql.connector.connect(**cfg)


def log_job(conn, job_name, status, rows=0, error=None, source_file=None, job_id=None):
    """
    Inserts or updates a row in etl_job_log.
    Call with status='STARTED' at the beginning of a job,
    then update to 'SUCCESS' or 'FAILED' at the end.
    """
    cursor = conn.cursor()
    if job_id is None:
        # Insert new job log entry
        cursor.execute("""
            INSERT INTO etl_job_log
                (job_name, status, rows_processed, start_time, source_file)
            VALUES (%s, %s, %s, %s, %s)
        """, (job_name, status, rows, datetime.now(), source_file))
        conn.commit()
        return cursor.lastrowid
    else:
        # Update existing job log entry
        cursor.execute("""
            UPDATE etl_job_log
            SET status = %s,
                rows_processed = %s,
                end_time = %s,
                error_message = %s
            WHERE job_id = %s
        """, (status, rows, datetime.now(), error, job_id))
        conn.commit()
        return job_id


def load_to_staging(rows, source_file=None):
    """
    Inserts a list of row dicts (from extract.py) into stg_orders.
    Skips rows whose order_id already exists in staging (idempotent load).

    Returns: number of rows actually inserted.
    """
    if not rows:
        logger.warning("No rows to load — empty data set.")
        return 0

    conn = get_connection(STAGING_DB)
    cursor = conn.cursor()
    job_id = log_job(conn, "load_staging", "STARTED",
                     source_file=str(source_file or RAW_CSV_FILE))

    # SQL to insert one row into stg_orders
    # We use INSERT IGNORE so duplicate order_ids are silently skipped
    insert_sql = """
        INSERT IGNORE INTO stg_orders (
            order_id, customer_name, customer_email, customer_phone,
            restaurant_name, restaurant_city, food_item, category,
            quantity, unit_price, total_amount,
            order_date, delivery_date, order_status,
            payment_method, delivery_address, driver_name, rating,
            source_file
        ) VALUES (
            %(order_id)s, %(customer_name)s, %(customer_email)s, %(customer_phone)s,
            %(restaurant_name)s, %(restaurant_city)s, %(food_item)s, %(category)s,
            %(quantity)s, %(unit_price)s, %(total_amount)s,
            %(order_date)s, %(delivery_date)s, %(order_status)s,
            %(payment_method)s, %(delivery_address)s, %(driver_name)s, %(rating)s,
            %(source_file)s
        )
    """

    inserted = 0
    errors = 0

    for row in rows:
        # Add the source_file metadata to each row
        row["source_file"] = str(source_file or RAW_CSV_FILE)
        # Replace empty strings with None so MySQL stores NULL
        row = {k: (v if v != '' else None) for k, v in row.items()}
        try:
            cursor.execute(insert_sql, row)
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            errors += 1
            logger.warning(f"Failed to insert order_id={row.get('order_id')}: {e}")

    conn.commit()

    if errors > 0:
        log_job(conn, "load_staging", "FAILED", rows=inserted,
                error=f"{errors} rows failed to insert", job_id=job_id)
        logger.error(f"Load staging finished with {errors} errors. {inserted} rows inserted.")
    else:
        log_job(conn, "load_staging", "SUCCESS", rows=inserted, job_id=job_id)
        logger.info(f"Load staging SUCCESS: {inserted} rows inserted into stg_orders.")

    cursor.close()
    conn.close()
    return inserted


if __name__ == "__main__":
    # Test this module standalone:
    #   python load_staging.py
    from extract import extract_from_csv
    data = extract_from_csv()
    count = load_to_staging(data)
    print(f"Inserted {count} rows into staging.")
