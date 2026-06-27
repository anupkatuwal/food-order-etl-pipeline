# ============================================================
# FILE: extract.py
# PURPOSE: Extract (read) raw data from the CSV file.
#          This is the "E" in ETL.
#
# In a real pipeline, this step might read from:
#   - A website API (e.g. Uber Eats order export)
#   - An FTP server where files are dropped daily
#   - An S3 bucket in AWS
# For this project we simulate it with a local CSV file.
# ============================================================

import csv
import logging
from pathlib import Path
from config import RAW_CSV_FILE

# Set up logging so we can see what's happening when we run
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def extract_from_csv(filepath=None):
    """
    Reads the raw CSV file and returns a list of dictionaries.
    Each dictionary represents one order row.

    Example output:
    [
      {'order_id': '1001', 'customer_name': 'Alice Johnson', ...},
      {'order_id': '1002', 'customer_name': 'Bob Smith', ...},
      ...
    ]
    """
    if filepath is None:
        filepath = RAW_CSV_FILE
    filepath = Path(filepath)  # accept both str and Path

    if not filepath.exists():
        logger.error(f"CSV file not found: {filepath}")
        raise FileNotFoundError(f"CSV file not found: {filepath}")

    rows = []
    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)  # DictReader maps each row to a dict using header names
        for row in reader:
            # Strip whitespace from all values
            cleaned_row = {k: v.strip() for k, v in row.items()}
            rows.append(cleaned_row)

    logger.info(f"Extracted {len(rows)} rows from {filepath.name}")
    return rows


if __name__ == "__main__":
    # Run this file directly to test extraction:
    #   python extract.py
    data = extract_from_csv()
    print(f"First row sample: {data[0]}")
    print(f"Total rows: {len(data)}")
