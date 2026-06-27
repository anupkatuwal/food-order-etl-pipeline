# Power BI Dashboard Setup Guide

## Prerequisites
- Power BI Desktop installed (free download: https://powerbi.microsoft.com/desktop)
- MySQL Connector/NET installed (download from https://dev.mysql.com/downloads/connector/net/)
- ETL pipeline has been run at least once (warehouse has data)

---

## Step 1 — Install MySQL Connector for Power BI

Power BI needs a driver to talk to MySQL.

1. Go to https://dev.mysql.com/downloads/connector/net/
2. Download **MySQL Connector/NET** (the Windows installer)
3. Run the installer with default settings
4. Restart Power BI Desktop after installation

---

## Step 2 — Connect Power BI to MySQL

1. Open **Power BI Desktop**
2. Click **Home → Get Data → More...**
3. In the search box type `MySQL` and select **MySQL database**
4. Click **Connect**
5. Enter:
   - **Server**: `localhost`
   - **Database**: `food_order_warehouse`
6. Click **OK**
7. When prompted for credentials:
   - Select **Database** authentication
   - Enter your MySQL username (e.g. `root`) and password
8. Click **Connect**

---

## Step 3 — Load the Tables

The Navigator window will show all tables in `food_order_warehouse`.

Check the box next to each of these tables:
- ✅ `dim_customers`
- ✅ `dim_restaurants`
- ✅ `dim_food_items`
- ✅ `dim_date`
- ✅ `fact_orders`

Click **Load** (not Transform, unless you want to make changes first).

---

## Step 4 — Set Up Relationships (Star Schema)

Power BI may auto-detect relationships. Verify them manually:

1. Click the **Model** view icon (left sidebar, looks like a network)
2. You should see the tables. Draw or verify these relationships:
   - `fact_orders[customer_key]` → `dim_customers[customer_key]`
   - `fact_orders[restaurant_key]` → `dim_restaurants[restaurant_key]`
   - `fact_orders[food_item_key]` → `dim_food_items[food_item_key]`
   - `fact_orders[order_date_key]` → `dim_date[date_key]`

3. For each relationship, ensure:
   - Cardinality: **Many to one (*:1)**
   - Cross filter direction: **Single**

---

## Step 5 — Build Your Dashboard

### Suggested Visuals

**1. Total Revenue KPI Card**
- Visual: Card
- Field: `fact_orders[total_amount]` → Aggregation: Sum
- Title: "Total Revenue"

**2. Revenue by Restaurant (Bar Chart)**
- Visual: Clustered Bar Chart
- X-Axis: `dim_restaurants[restaurant_name]`
- Y-Axis: `fact_orders[total_amount]` (Sum)
- Title: "Revenue by Restaurant"

**3. Orders by Category (Donut Chart)**
- Visual: Donut Chart
- Legend: `dim_food_items[category]`
- Values: `fact_orders[order_key]` (Count)
- Title: "Orders by Food Category"

**4. Daily Revenue Trend (Line Chart)**
- Visual: Line Chart
- X-Axis: `dim_date[full_date]`
- Y-Axis: `fact_orders[total_amount]` (Sum)
- Title: "Daily Revenue Trend"

**5. Order Status Breakdown (Pie Chart)**
- Visual: Pie Chart
- Legend: `fact_orders[order_status]`
- Values: `fact_orders[order_key]` (Count)

**6. Top Customers Table**
- Visual: Table
- Columns: `dim_customers[customer_name]`, Count of orders, Sum of `total_amount`
- Sort by total_amount descending

---

## Step 6 — Add a Slicer (Filter)

Slicers let users interactively filter the dashboard.

1. Add a **Slicer** visual
2. Field: `dim_date[month_name]`
3. Now clicking a month filters all visuals on the page

Add another slicer:
- Field: `dim_restaurants[restaurant_city]`

---

## Step 7 — Refresh Data

When you run the ETL pipeline again with new data:

1. In Power BI Desktop: click **Home → Refresh**
2. All visuals will update with the latest warehouse data

To schedule automatic refresh (requires Power BI Service / Pro):
1. Publish your report to Power BI Service
2. Set up a scheduled refresh under dataset settings

---

## DAX Measures (Optional — Advanced)

DAX is Power BI's formula language. Add these measures for richer analytics:

```dax
-- Average Order Value
Avg Order Value = AVERAGE(fact_orders[total_amount])

-- Cancellation Rate
Cancellation Rate =
DIVIDE(
    COUNTROWS(FILTER(fact_orders, fact_orders[order_status] = "Cancelled")),
    COUNTROWS(fact_orders)
) * 100

-- Month-over-Month Revenue Change
MoM Revenue Change =
VAR CurrentMonth = SUM(fact_orders[total_amount])
VAR PrevMonth = CALCULATE(
    SUM(fact_orders[total_amount]),
    DATEADD(dim_date[full_date], -1, MONTH)
)
RETURN DIVIDE(CurrentMonth - PrevMonth, PrevMonth) * 100
```

To add a measure:
1. Right-click a table in the Fields pane → **New measure**
2. Type or paste the DAX formula
3. Press Enter

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "MySQL database" not in Get Data list | Install MySQL Connector/NET and restart Power BI |
| Connection refused | Make sure MySQL server is running (`net start MySQL80` in CMD) |
| No data in visuals | Check that the ETL pipeline ran and warehouse has rows |
| Relationships missing | Go to Model view and manually draw the FK relationships |
