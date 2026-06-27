# ============================================================
# FILE: config.py
# PURPOSE: Central configuration for the ETL pipeline.
#
# WHY A SEPARATE CONFIG FILE?
# Keeping connection details in one place means if your
# MySQL password changes, you only update it here — not in
# every script. Never hardcode credentials in multiple places.
# ============================================================

import os

# ── MySQL Connection Settings ─────────────────────────────
# Change these to match your MySQL installation.
# If you installed MySQL locally with default settings,
# HOST is usually 'localhost' and PORT is 3306.

DB_CONFIG = {
    "host":     os.getenv("MYSQL_HOST", "localhost"),
    "port":     int(os.getenv("MYSQL_PORT", 3306)),
    "user":     os.getenv("MYSQL_USER", "root"),       # ← change to your MySQL username
    "password": os.getenv("MYSQL_PASSWORD", ""),       # ← change to your MySQL password
}

# Staging database name (created in 01_create_staging_db.sql)
STAGING_DB = "food_order_staging"

# Warehouse database name (created in 02_create_warehouse_db.sql)
WAREHOUSE_DB = "food_order_warehouse"

# ── File Paths ────────────────────────────────────────────
# Path to the raw CSV data file
import pathlib

# This resolves to the /data/raw/ folder relative to the project root
PROJECT_ROOT = pathlib.Path(__file__).parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
RAW_CSV_FILE = RAW_DATA_DIR / "food_orders_raw.csv"
