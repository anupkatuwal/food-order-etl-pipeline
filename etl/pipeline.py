#!/usr/bin/env python3
# ============================================================
# FILE: pipeline.py
# PURPOSE: The main ETL runner. Orchestrates the full pipeline:
#          Extract → Load Staging → Transform → Warehouse
#
# HOW TO RUN:
#   cd etl/
#   python pipeline.py
#
# WHAT HAPPENS STEP BY STEP:
#   1. Read raw CSV data (extract.py)
#   2. Insert rows into stg_orders (load_staging.py)
#   3. Call MySQL stored procedures to populate warehouse (transform.py)
#   4. Print a summary
#
# In production, this script would be scheduled to run
# automatically (e.g., via cron job or Apache Airflow).
# ============================================================

import sys
import logging
from datetime import datetime

from extract import extract_from_csv
from load_staging import load_to_staging
from transform import run_transformations, get_staging_row_count
from config import RAW_CSV_FILE

# Configure logging — all modules share this format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),          # print to console
        logging.FileHandler("pipeline_run.log"),    # also write to a log file
    ]
)
logger = logging.getLogger(__name__)


def run_pipeline():
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("  FOOD ORDER ETL PIPELINE — STARTING")
    logger.info("=" * 60)

    # ── STEP 1: EXTRACT ───────────────────────────────────
    logger.info("STEP 1: Extracting data from CSV...")
    try:
        raw_rows = extract_from_csv(RAW_CSV_FILE)
        logger.info(f"  ✓ Extracted {len(raw_rows)} rows")
    except FileNotFoundError as e:
        logger.error(f"  ✗ Extract failed: {e}")
        sys.exit(1)

    # ── STEP 2: LOAD INTO STAGING ─────────────────────────
    logger.info("STEP 2: Loading data into staging database...")
    inserted = load_to_staging(raw_rows, source_file=RAW_CSV_FILE)
    logger.info(f"  ✓ {inserted} new rows loaded into stg_orders")

    # Check how many unprocessed rows are waiting
    pending = get_staging_row_count()
    logger.info(f"  ✓ {pending} unprocessed rows in staging (including previous runs)")

    if pending == 0:
        logger.info("  No new data to transform. Pipeline complete.")
        return

    # ── STEP 3: TRANSFORM → WAREHOUSE ────────────────────
    logger.info("STEP 3: Running transformations (staging → warehouse)...")
    success = run_transformations()

    if success:
        logger.info("  ✓ Warehouse updated successfully")
    else:
        logger.error("  ✗ Transformation failed — check etl_job_log in MySQL")
        sys.exit(1)

    # ── SUMMARY ───────────────────────────────────────────
    duration = (datetime.now() - start_time).total_seconds()
    logger.info("=" * 60)
    logger.info(f"  PIPELINE COMPLETE in {duration:.1f} seconds")
    logger.info(f"  Rows extracted  : {len(raw_rows)}")
    logger.info(f"  Rows to staging : {inserted}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_pipeline()
