# ============================================================
# FILE: transform.py
# PURPOSE: Call MySQL stored procedures to transform data
#          from staging → warehouse. This is the "T" in ETL.
#
# KEY CONCEPT:
# All the heavy transformation logic lives inside MySQL stored
# procedures (see sql/03_stored_procedures.sql).
# Python's job here is simply to call those procedures in order
# and handle any errors.
#
# Why keep transform logic in SQL (not Python)?
#   - SQL is much faster for set-based operations on large data
#   - The logic stays close to the database (easier for DBAs)
#   - Easier to test SQL procedures independently
# ============================================================

import mysql.connector
import logging
from config import DB_CONFIG, STAGING_DB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def get_connection(database=None):
    cfg = DB_CONFIG.copy()
    if database:
        cfg["database"] = database
    return mysql.connector.connect(**cfg)


def run_transformations():
    """
    Calls sp_run_full_etl, the master stored procedure that:
      1. Loads dim_customers
      2. Loads dim_restaurants
      3. Loads dim_food_items
      4. Loads fact_orders
      5. Marks staging rows as processed

    Returns True on success, False on failure.
    """
    conn = get_connection(STAGING_DB)
    cursor = conn.cursor()

    try:
        logger.info("Calling sp_run_full_etl stored procedure...")

        # CALL executes the stored procedure in MySQL
        cursor.callproc("sp_run_full_etl")

        # Stored procedures can return result sets — fetch them to see status messages
        for result in cursor.stored_results():
            rows = result.fetchall()
            for row in rows:
                logger.info(f"Procedure result: {row[0]}")

        conn.commit()
        logger.info("Transformation complete — warehouse is up to date.")
        return True

    except mysql.connector.Error as e:
        conn.rollback()
        logger.error(f"Transformation FAILED: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


def get_staging_row_count():
    """
    Returns the count of unprocessed rows in staging.
    Useful to check before running transformations.
    """
    conn = get_connection(STAGING_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM stg_orders WHERE is_processed = 0")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count


if __name__ == "__main__":
    # Test this module standalone:
    #   python transform.py
    pending = get_staging_row_count()
    print(f"Unprocessed staging rows: {pending}")
    if pending > 0:
        success = run_transformations()
        print("Transform successful!" if success else "Transform failed — check logs.")
    else:
        print("Nothing to transform.")
