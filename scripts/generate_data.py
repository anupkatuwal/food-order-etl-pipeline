#!/usr/bin/env python3
"""
generate_data.py
────────────────
Generates realistic fake food order data and writes it to
data/raw/food_orders_raw.csv

Usage:
    python scripts/generate_data.py              # generates 200 rows (default)
    python scripts/generate_data.py --rows 500   # generates 500 rows

This script uses only the Python standard library — no pip install needed.
"""

import csv
import random
import argparse
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

RESTAURANTS = [
    ("Pizza Palace",    "New York"),
    ("Burger Barn",     "Los Angeles"),
    ("Sushi Stop",      "Chicago"),
    ("Taco Town",       "Houston"),
    ("Noodle House",    "Seattle"),
    ("Curry Corner",    "San Francisco"),
    ("Grill Master",    "Phoenix"),
    ("Veggie Delight",  "Austin"),
    ("BBQ Brothers",    "Dallas"),
    ("Pasta Primo",     "Miami"),
]

MENU = {
    "Pizza Palace":   [("Pepperoni Pizza","Pizza",12.99), ("Margherita Pizza","Pizza",11.99),
                       ("BBQ Chicken Pizza","Pizza",13.99), ("Vegetarian Pizza","Pizza",12.49),
                       ("Four Cheese Pizza","Pizza",14.99)],
    "Burger Barn":    [("Classic Cheeseburger","Burger",9.99), ("BBQ Bacon Burger","Burger",11.49),
                       ("Veggie Burger","Burger",8.99), ("Double Smash Burger","Burger",13.99),
                       ("Mushroom Swiss Burger","Burger",10.99)],
    "Sushi Stop":     [("Salmon Roll","Sushi",8.50), ("Tuna Sashimi","Sushi",14.00),
                       ("California Roll","Sushi",7.50), ("Dragon Roll","Sushi",13.00),
                       ("Spicy Tuna Roll","Sushi",9.50)],
    "Taco Town":      [("Chicken Tacos","Mexican",5.99), ("Beef Burrito","Mexican",8.99),
                       ("Veggie Tacos","Mexican",5.49), ("Nachos","Mexican",6.99),
                       ("Quesadilla","Mexican",7.49)],
    "Noodle House":   [("Pad Thai","Asian",10.99), ("Ramen","Asian",12.50),
                       ("Pho","Asian",11.99), ("Dumplings","Asian",8.99),
                       ("Fried Rice","Asian",9.99)],
    "Curry Corner":   [("Butter Chicken","Indian",13.99), ("Lamb Biryani","Indian",15.99),
                       ("Palak Paneer","Indian",11.99), ("Chicken Tikka Masala","Indian",14.49),
                       ("Dal Makhani","Indian",10.99)],
    "Grill Master":   [("Ribeye Steak","Grill",24.99), ("Grilled Salmon","Grill",19.99),
                       ("BBQ Ribs","Grill",21.99), ("Grilled Chicken","Grill",14.99),
                       ("Lamb Chops","Grill",22.99)],
    "Veggie Delight": [("Buddha Bowl","Healthy",11.99), ("Quinoa Salad","Healthy",9.99),
                       ("Avocado Toast","Healthy",8.99), ("Green Smoothie Bowl","Healthy",10.49),
                       ("Lentil Soup","Healthy",7.99)],
    "BBQ Brothers":   [("Pulled Pork Sandwich","BBQ",12.99), ("Smoked Brisket","BBQ",17.99),
                       ("BBQ Chicken Wings","BBQ",13.99), ("Loaded Fries","BBQ",8.99),
                       ("Coleslaw Plate","BBQ",6.99)],
    "Pasta Primo":    [("Spaghetti Carbonara","Italian",13.99), ("Fettuccine Alfredo","Italian",12.99),
                       ("Penne Arrabbiata","Italian",11.99), ("Lasagna","Italian",14.99),
                       ("Risotto","Italian",15.99)],
}

CUSTOMERS = [
    ("Alice Johnson","alice@email.com","555-1001","123 Main St, New York"),
    ("Bob Smith","bob@email.com","555-1002","456 Oak Ave, Los Angeles"),
    ("Carol White","carol@email.com","555-1003","789 Elm St, Chicago"),
    ("David Lee","david@email.com","555-1004","321 Pine Rd, New York"),
    ("Emma Davis","emma@email.com","555-1005","654 Cedar Blvd, Houston"),
    ("Frank Miller","frank@email.com","555-1006","987 Maple Dr, Los Angeles"),
    ("Grace Wilson","grace@email.com","555-1007","147 Birch Ln, Chicago"),
    ("Henry Moore","henry@email.com","555-1008","258 Walnut Ave, Houston"),
    ("Iris Taylor","iris@email.com","555-1009","369 Spruce St, Seattle"),
    ("Jack Anderson","jack@email.com","555-1010","741 Ash Blvd, New York"),
    ("Karen Thomas","karen@email.com","555-1011","852 Hickory Rd, Los Angeles"),
    ("Liam Jackson","liam@email.com","555-1012","963 Poplar Ave, Seattle"),
    ("Mia Harris","mia@email.com","555-1013","159 Elm Park, Chicago"),
    ("Noah Martin","noah@email.com","555-1014","267 Oak Creek, Houston"),
    ("Olivia Garcia","olivia@email.com","555-1015","375 Pine Hill, New York"),
    ("Paul Rodriguez","paul@email.com","555-1016","483 Maple Court, Los Angeles"),
    ("Quinn Lewis","quinn@email.com","555-1017","591 Birch Road, Seattle"),
    ("Rachel Lee","rachel@email.com","555-1018","699 Walnut Blvd, Chicago"),
    ("Sam Walker","sam@email.com","555-1019","807 Spruce Lane, Houston"),
    ("Tina Hall","tina@email.com","555-1020","915 Ash Street, New York"),
    ("Uma Clark","uma@email.com","555-1021","124 Cedar Ave, San Francisco"),
    ("Victor Adams","victor@email.com","555-1022","235 Elm Drive, Phoenix"),
    ("Wendy Brown","wendy@email.com","555-1023","346 Oak Blvd, Austin"),
    ("Xander Young","xander@email.com","555-1024","457 Maple St, Dallas"),
    ("Yara King","yara@email.com","555-1025","568 Pine Ave, Miami"),
    ("Zoe Scott","zoe@email.com","555-1026","679 Birch Court, San Francisco"),
    ("Aaron Hill","aaron@email.com","555-1027","780 Walnut Rd, Phoenix"),
    ("Bella Turner","bella@email.com","555-1028","891 Spruce Blvd, Austin"),
    ("Carlos Evans","carlos@email.com","555-1029","902 Ash Lane, Dallas"),
    ("Diana Collins","diana@email.com","555-1030","113 Cedar Park, Miami"),
]

DRIVERS = {
    "New York":       ["Mike Ross","Sara Patel","John Wu"],
    "Los Angeles":    ["Sara Lee","James Kim","Nina Lopez"],
    "Chicago":        ["Tom Brown","Amy Chen","Kevin Park"],
    "Houston":        ["Lisa Park","Ryan Davis","Maria Garcia"],
    "Seattle":        ["Amy Chen","Chris Johnson","Priya Kumar"],
    "San Francisco":  ["David Kim","Sophie Brown","Alex Zhang"],
    "Phoenix":        ["Jake Miller","Rebecca Jones","Carlos Diaz"],
    "Austin":         ["Emma Wilson","Brandon Lee","Natalie Chen"],
    "Dallas":         ["Tyler Johnson","Samantha Brown","Marcus Davis"],
    "Miami":          ["Isabella Martinez","Ryan Thompson","Chloe Anderson"],
}

PAYMENT_METHODS = ["Credit Card","Debit Card","Cash","PayPal","Apple Pay","Google Pay"]
STATUSES        = ["Delivered","Delivered","Delivered","Delivered","Cancelled","Pending"]


def make_order(order_id: int, base_date: datetime) -> dict:
    customer = random.choice(CUSTOMERS)
    restaurant_name, restaurant_city = random.choice(RESTAURANTS)
    food_item, category, unit_price = random.choice(MENU[restaurant_name])
    quantity  = random.randint(1, 4)
    status    = random.choice(STATUSES)
    payment   = random.choice(PAYMENT_METHODS)
    order_dt  = base_date + timedelta(
        days=random.randint(0, 179),
        hours=random.randint(10, 22),
        minutes=random.randint(0, 59)
    )

    if status == "Delivered":
        delivery_dt = order_dt + timedelta(minutes=random.randint(25, 75))
        driver      = random.choice(DRIVERS.get(restaurant_city, ["Unknown"]))
        rating      = random.choices([3, 4, 4, 5, 5, 5], k=1)[0]
    else:
        delivery_dt = None
        driver      = None
        rating      = None

    return {
        "order_id":         order_id,
        "customer_name":    customer[0],
        "customer_email":   customer[1],
        "customer_phone":   customer[2],
        "restaurant_name":  restaurant_name,
        "restaurant_city":  restaurant_city,
        "food_item":        food_item,
        "category":         category,
        "quantity":         quantity,
        "unit_price":       unit_price,
        "total_amount":     round(quantity * unit_price, 2),
        "order_date":       order_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "delivery_date":    delivery_dt.strftime("%Y-%m-%d %H:%M:%S") if delivery_dt else "",
        "order_status":     status,
        "payment_method":   payment,
        "delivery_address": customer[3],
        "driver_name":      driver or "",
        "rating":           rating or "",
    }


def generate(n_rows: int, output_path: Path):
    base_date = datetime(2024, 1, 1)
    orders = [make_order(1001 + i, base_date) for i in range(n_rows)]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(orders[0].keys())

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(orders)

    print(f"✓ Generated {n_rows} orders → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate fake food order data")
    parser.add_argument("--rows", type=int, default=200, help="Number of orders (default: 200)")
    parser.add_argument("--output", type=str, default="data/raw/food_orders_raw.csv")
    args = parser.parse_args()
    generate(args.rows, Path(args.output))
