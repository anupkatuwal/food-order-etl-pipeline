# ============================================================
# Food Order ETL Pipeline — Makefile
# Usage: make <target>
# ============================================================

.PHONY: help install generate run test clean

help:
	@echo ""
	@echo "  Food Order ETL Pipeline"
	@echo "  ─────────────────────────────────────────"
	@echo "  make install    Install Python dependencies"
	@echo "  make generate   Generate 200 sample orders"
	@echo "  make run        Run the full ETL pipeline"
	@echo "  make test       Run unit tests"
	@echo "  make clean      Remove logs and cache files"
	@echo ""

install:
	@echo "Installing Python dependencies..."
	pip install -r etl/requirements.txt
	@echo "✓ Done"

generate:
	@echo "Generating 200 sample orders..."
	python scripts/generate_data.py --rows 200
	@echo "✓ Data written to data/raw/food_orders_raw.csv"

run:
	@echo "Running ETL pipeline..."
	cd etl && python pipeline.py

test:
	@echo "Running tests..."
	pytest tests/ -v

clean:
	@echo "Cleaning up..."
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	rm -f etl/pipeline_run.log
	@echo "✓ Done"
