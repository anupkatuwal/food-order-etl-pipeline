"""
tests/test_extract.py
─────────────────────
Unit tests for the Extract phase of the ETL pipeline.

These tests verify that:
  - The CSV file is read correctly
  - Required columns are present
  - Data types are as expected
  - Row counts match

Run with:
    pytest tests/ -v
"""

import sys
import os
import csv
import pytest
from pathlib import Path

# Make sure the etl/ folder is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "etl"))

EXPECTED_COLUMNS = [
    "order_id", "customer_name", "customer_email", "customer_phone",
    "restaurant_name", "restaurant_city", "food_item", "category",
    "quantity", "unit_price", "total_amount", "order_date",
    "delivery_date", "order_status", "payment_method",
    "delivery_address", "driver_name", "rating"
]

CSV_PATH = Path(__file__).parent.parent / "data" / "raw" / "food_orders_raw.csv"


@pytest.fixture(scope="module")
def raw_data():
    """Load CSV data once for all tests in this module."""
    assert CSV_PATH.exists(), f"CSV file not found at {CSV_PATH}"
    with open(CSV_PATH, newline="") as f:
        return list(csv.DictReader(f))


class TestCSVStructure:
    def test_file_exists(self):
        """CSV file must exist in the expected location."""
        assert CSV_PATH.exists(), f"Missing: {CSV_PATH}"

    def test_has_rows(self, raw_data):
        """CSV must contain at least one data row."""
        assert len(raw_data) > 0, "CSV is empty"

    def test_minimum_row_count(self, raw_data):
        """Should have at least 20 rows for meaningful analysis."""
        assert len(raw_data) >= 20, f"Expected >= 20 rows, got {len(raw_data)}"

    def test_expected_columns(self, raw_data):
        """All required columns must be present."""
        actual_cols = set(raw_data[0].keys())
        for col in EXPECTED_COLUMNS:
            assert col in actual_cols, f"Missing column: '{col}'"

    def test_no_extra_unexpected_columns(self, raw_data):
        """Column count should match expected."""
        actual = set(raw_data[0].keys())
        expected = set(EXPECTED_COLUMNS)
        assert actual == expected, f"Column mismatch. Extra: {actual-expected}, Missing: {expected-actual}"


class TestDataQuality:
    def test_order_ids_not_empty(self, raw_data):
        """Every row must have an order_id."""
        for i, row in enumerate(raw_data):
            assert row["order_id"].strip(), f"Empty order_id on row {i+2}"

    def test_order_ids_unique(self, raw_data):
        """order_id values must be unique."""
        ids = [r["order_id"] for r in raw_data]
        assert len(ids) == len(set(ids)), "Duplicate order_ids found"

    def test_order_ids_are_numeric(self, raw_data):
        """order_id should be parseable as an integer."""
        for row in raw_data:
            assert row["order_id"].isdigit(), f"Non-numeric order_id: {row['order_id']}"

    def test_emails_contain_at_sign(self, raw_data):
        """customer_email must contain '@'."""
        for row in raw_data:
            if row["customer_email"]:
                assert "@" in row["customer_email"], \
                    f"Invalid email: {row['customer_email']} (order {row['order_id']})"

    def test_total_amount_is_positive(self, raw_data):
        """total_amount must be a positive number."""
        for row in raw_data:
            if row["total_amount"]:
                val = float(row["total_amount"])
                assert val > 0, f"Non-positive total_amount: {val} (order {row['order_id']})"

    def test_unit_price_is_positive(self, raw_data):
        """unit_price must be a positive number."""
        for row in raw_data:
            if row["unit_price"]:
                val = float(row["unit_price"])
                assert val > 0, f"Non-positive unit_price: {val} (order {row['order_id']})"

    def test_quantity_is_positive_integer(self, raw_data):
        """quantity must be a positive integer."""
        for row in raw_data:
            if row["quantity"]:
                val = int(row["quantity"])
                assert val > 0, f"Non-positive quantity: {val} (order {row['order_id']})"

    def test_total_equals_qty_times_price(self, raw_data):
        """total_amount should equal quantity × unit_price (within rounding)."""
        for row in raw_data:
            if row["quantity"] and row["unit_price"] and row["total_amount"]:
                expected = round(int(row["quantity"]) * float(row["unit_price"]), 2)
                actual   = round(float(row["total_amount"]), 2)
                assert abs(expected - actual) < 0.02, \
                    f"Mismatch order {row['order_id']}: {row['quantity']}×{row['unit_price']}={expected}, got {actual}"

    def test_order_status_valid_values(self, raw_data):
        """order_status must be one of the allowed values."""
        valid = {"Delivered", "Cancelled", "Pending"}
        for row in raw_data:
            if row["order_status"]:
                assert row["order_status"] in valid, \
                    f"Invalid status '{row['order_status']}' (order {row['order_id']})"

    def test_rating_in_valid_range(self, raw_data):
        """rating must be 1–5 when present."""
        for row in raw_data:
            if row["rating"]:
                val = int(row["rating"])
                assert 1 <= val <= 5, f"Rating out of range: {val} (order {row['order_id']})"

    def test_cancelled_orders_have_no_driver(self, raw_data):
        """Cancelled orders should not have a driver assigned."""
        for row in raw_data:
            if row["order_status"] == "Cancelled":
                assert not row["driver_name"].strip(), \
                    f"Cancelled order {row['order_id']} has driver '{row['driver_name']}'"

    def test_delivered_orders_have_driver(self, raw_data):
        """Delivered orders must have a driver and delivery_date."""
        for row in raw_data:
            if row["order_status"] == "Delivered":
                assert row["driver_name"].strip(), \
                    f"Delivered order {row['order_id']} has no driver"
                assert row["delivery_date"].strip(), \
                    f"Delivered order {row['order_id']} has no delivery_date"


class TestExtractModule:
    def test_extract_function_returns_list(self):
        """extract_from_csv() should return a list of dicts."""
        from extract import extract_from_csv
        result = extract_from_csv(str(CSV_PATH))
        assert isinstance(result, list)
        assert len(result) > 0

    def test_extract_returns_correct_count(self, raw_data):
        """extract_from_csv() row count should match direct CSV count."""
        from extract import extract_from_csv
        result = extract_from_csv(str(CSV_PATH))
        assert len(result) == len(raw_data)

    def test_extract_raises_on_missing_file(self):
        """extract_from_csv() should raise FileNotFoundError for missing files."""
        from extract import extract_from_csv
        with pytest.raises(FileNotFoundError):
            extract_from_csv("nonexistent_file.csv")
