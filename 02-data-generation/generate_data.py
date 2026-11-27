"""
Food Delivery Platform Analytics - synthetic data generator
============================================================
Generates realistic fake data and loads it into the FoodDeliveryDB database
created by 01_create_schema.sql.

Usage
-----
    pip install pyodbc
    python generate_data.py --dry-run     # generate + validate only, no database needed
    python generate_data.py               # generate and load into SQL Server

Notes
-----
* Uses only the standard library plus pyodbc, so there is little to install.
* The random seed is fixed, so everyone running the script gets the same data.
* Re-running the script clears the tables first, then reloads them.
* Amounts are in a generic currency unit.
"""

import argparse
import math
import random
from datetime import date, datetime, time, timedelta

# ----------------------------------------------------------------------
# CONFIGURATION - change these to fit your setup
# ----------------------------------------------------------------------
SERVER = "localhost"          # e.g. "localhost", r".\SQLEXPRESS", or your PC name
DATABASE = "FoodDeliveryDB"

SEED = 42
N_CUSTOMERS = 2000
N_RESTAURANTS = 150
N_COURIERS = 60
START_DATE = date(2025, 1, 1)    # first day with orders
END_DATE = date(2026, 10, 31)    # last day with orders

# ----------------------------------------------------------------------
# REFERENCE DATA
# ----------------------------------------------------------------------
# city -> share of customers / restaurants / couriers
CITIES = {"Tehran": 0.45, "Isfahan": 0.15,
        "Shiraz": 0.15, "Mashhad": 0.15, "Tabriz": 0.10}

# cuisine -> list of (menu item, typical price)
MENUS = {
    "Persian": [("Chicken Kabob Plate", 11), ("Ghormeh Sabzi", 9), ("Fesenjan", 10), ("Zereshk Polo", 9),
                ("Barg Kabob", 14), ("Mirza Ghasemi", 6), ("Abgoosht", 8), ("Salad Shirazi", 3), ("Doogh", 1.5)],
    "Fast Food": [("Fried Chicken Box", 8), ("Chicken Nuggets", 5), ("French Fries", 3), ("Hot Dog", 4),
                ("Chicken Wrap", 6), ("Onion Rings", 3.5), ("Soda", 1.5), ("Milkshake", 4)],
    "Pizza": [("Margherita", 9), ("Pepperoni", 11), ("Veggie Pizza", 10), ("BBQ Chicken Pizza", 12),
            ("Four Cheese", 12), ("Garlic Bread", 4), ("Caesar Salad", 6), ("Soda", 1.5)],
    "Burger": [("Classic Burger", 8), ("Cheeseburger", 9), ("Double Burger", 12), ("Chicken Burger", 8),
            ("Veggie Burger", 8), ("Sweet Potato Fries", 4), ("French Fries", 3), ("Milkshake", 4)],
    "Italian": [("Spaghetti Bolognese", 10), ("Fettuccine Alfredo", 11), ("Lasagna", 12), ("Penne Arrabbiata", 9),
                ("Risotto", 12), ("Tiramisu", 6), ("Bruschetta", 5), ("Minestrone", 6)],
    "Sushi": [("Salmon Roll", 10), ("Tuna Roll", 11), ("California Roll", 9), ("Veggie Roll", 8),
            ("Nigiri Set", 14), ("Miso Soup", 3), ("Edamame", 4), ("Dragon Roll", 13)],
    "Kebab": [("Kebab Koobideh", 10), ("Joojeh Kabob", 11), ("Shishlik", 16), ("Chicken Doner", 7),
            ("Beef Doner", 8), ("Grilled Tomato", 1.5), ("Rice Plate", 4), ("Ayran", 1.5)],
    "Healthy": [("Chicken Salad Bowl", 9), ("Quinoa Bowl", 10), ("Avocado Toast", 7), ("Green Smoothie", 5),
                ("Grilled Salmon", 15), ("Lentil Soup", 5), ("Falafel Wrap", 7), ("Fruit Cup", 4)],
    "Dessert": [("Chocolate Cake", 6), ("Cheesecake", 6.5), ("Ice Cream Cup", 4), ("Baklava", 5),
                ("Brownie", 4), ("Crepe", 6), ("Waffle", 7), ("Cookie Box", 5)],
    "Cafe": [("Cappuccino", 3.5), ("Latte", 4), ("Espresso", 2.5), ("Iced Coffee", 4), ("Croissant", 3.5),
            ("Club Sandwich", 7), ("Blueberry Muffin", 3.5), ("Hot Chocolate", 4)],
}

NAME_PREFIX = ["Golden", "Royal", "Fresh", "Urban", "Happy", "Spicy", "Cozy", "Grand", "Sunny", "Blue",
            "Green", "Red", "Old Town", "Little", "Super", "Tasty", "Hot", "Smart", "Rose", "Lucky"]
NAME_SUFFIX = {"Persian": "Kitchen", "Fast Food": "Express", "Pizza": "Pizzeria", "Burger": "Burger Bar",
            "Italian": "Trattoria", "Sushi": "Sushi House", "Kebab": "Kebab House", "Healthy": "Bowl",
            "Dessert": "Sweets", "Cafe": "Cafe"}

FIRST_NAMES = ["Ali", "Sara", "Reza", "Mina", "Hossein", "Narges", "Amir", "Zahra", "Mehdi", "Fatemeh",
            "Saeed", "Maryam", "Hamed", "Leila", "Omid", "Nazanin", "Kaveh", "Shirin", "Arash", "Parisa",
            "Farhad", "Elham", "Behnam", "Samira", "Peyman", "Negar", "Kian", "Azadeh", "Babak", "Roya"]
LAST_NAMES = ["Rezaei", "Mohammadi", "Karimi", "Ahmadi", "Hosseini", "Jafari", "Moradi", "Sadeghi", "Rahimi",
            "Ghasemi", "Hashemi", "Mousavi", "Kazemi", "Najafi", "Tavakoli", "Azizi", "Zare", "Farhadi",
            "Bagheri", "Shirazi"]

# (code, type, value, start, end)
PROMOTIONS = [
    ("WELCOME20", "Percent", 20, date(2025, 1, 1),
    date(2026, 12, 31)),   # first order only
    ("WEEKEND10", "Percent", 10, date(2025, 1, 1), date(2026, 12, 31)),
    ("SAVE3", "Fixed", 3, date(2025, 3, 1), date(2025, 4, 15)),
    ("SUMMER15", "Percent", 15, date(2025, 6, 1), date(2025, 8, 31)),
    ("LUNCH5", "Fixed", 5, date(2025, 9, 1), date(2025, 12, 31)),
    ("BLACKFRI30", "Percent", 30, date(2025, 11, 24), date(2025, 11, 30)),
    ("NEWYEAR15", "Percent", 15, date(2026, 1, 1), date(2026, 1, 10)),
    ("SPRING12", "Percent", 12, date(2026, 3, 1), date(2026, 5, 31)),
]

# Demand by hour of day (0-23): lunch peak around 12-13h, dinner peak around 19-21h
HOUR_WEIGHTS = [2, 1, 0.5, 0.3, 0.2, 0.3, 0.6, 1, 1.5, 1.8, 2.5, 5,
                9, 9, 5, 3, 3, 4, 6, 9, 10, 8, 5, 3]

COMMENTS = {
    5: ["Great food and fast delivery!", "Excellent, will order again.", "Hot and delicious."],
    4: ["Good food, arrived on time.", "Tasty, a bit pricey.", "Nice portion size."],
    3: ["Okay, nothing special.", "Food was lukewarm.", "Average experience."],
    2: ["Late delivery.", "Order was missing an item.", "Not worth the price."],
    1: ["Very late and cold.", "Terrible experience.", "Wrong order delivered."],
}


# ----------------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------------
def poisson(lam):
    """Random count with mean `lam` (number of orders a customer places)."""
    if lam <= 0:
        return 0
    if lam > 30:
        return max(0, round(random.gauss(lam, math.sqrt(lam))))
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        k += 1
        p *= random.random()
        if p <= limit:
            return k - 1


def build_day_weights():
    """Relative demand for each day: weekends busier, mild seasonality, business grows over time."""
    month_factor = {1: 1.00, 2: 0.95, 3: 1.00, 4: 1.00, 5: 1.00, 6: 0.95,
                    7: 0.95, 8: 0.95, 9: 1.00, 10: 1.05, 11: 1.10, 12: 1.15}
    weights, d = {}, START_DATE
    while d <= END_DATE:
        months_since_start = (d.year - START_DATE.year) * \
            12 + d.month - START_DATE.month
        weekend = 1.25 if d.weekday() in (4, 5) else 1.0          # Friday / Saturday
        weights[d] = month_factor[d.month] * \
            weekend * (1 + 0.02 * months_since_start)
        d += timedelta(days=1)
    return weights


def random_dt(day):
    hour = random.choices(range(24), weights=HOUR_WEIGHTS)[0]
    return datetime.combine(day, time(hour, random.randint(0, 59), random.randint(0, 59)))


def random_phone():
    return "09" + "".join(random.choice("0123456789") for _ in range(9))


def weighted_city_list(n):
    """n city names following CITIES shares; first len(CITIES) entries guarantee every city is present."""
    names, shares = list(CITIES), list(CITIES.values())
    result = [(c, True) for c in names] + [(c, False)
                                        for c in random.choices(names, shares, k=n - len(names))]
    random.shuffle(result)
    return result      # list of (city_name, is_founding)


# ----------------------------------------------------------------------
# DATA GENERATION
# ----------------------------------------------------------------------
def generate():
    day_weights = build_day_weights()
    max_day_weight = max(day_weights.values())

    def random_day(lo, hi):
        span = (hi - lo).days
        while True:
            day = lo + timedelta(days=random.randint(0, span))
            if random.random() <= day_weights[day] / max_day_weight:
                return day

    city_ids = {name: i + 1 for i, name in enumerate(CITIES)}
    cuisine_ids = {name: i + 1 for i, name in enumerate(MENUS)}

    t = {name: [] for name in ["Cities", "Cuisines", "Customers", "Restaurants", "MenuItems", "Couriers",
                            "Promotions", "Orders", "OrderItems", "Deliveries", "Reviews"]}
    t["Cities"] = [(cid, name) for name, cid in city_ids.items()]
    t["Cuisines"] = [(cid, name) for name, cid in cuisine_ids.items()]
    t["Promotions"] = [(i + 1, *p) for i, p in enumerate(PROMOTIONS)]

    # ---- Restaurants and menus -------------------------------------------------
    restaurants = {}
    menu_id = 0
    for rid, (city, founding) in enumerate(weighted_city_list(N_RESTAURANTS), start=1):
        cuisine = random.choice(list(MENUS))
        if founding or random.random() < 0.8:
            joined = START_DATE - timedelta(days=random.randint(30, 540))
        else:
            joined = START_DATE + \
                timedelta(days=random.randint(
                    0, (END_DATE - START_DATE).days - 60))
        name = f"{random.choice(NAME_PREFIX)} {NAME_SUFFIX[cuisine]}"
        restaurants[rid] = {
            "city": city, "joined": joined,
            "popularity": random.lognormvariate(0, 0.9),
            "quality": random.uniform(-0.5, 0.4),
            "menu": [],
        }
        t["Restaurants"].append((rid, name, cuisine_ids[cuisine], city_ids[city], joined,
                                1 if random.random() < 0.95 else 0))
        template = MENUS[cuisine]
        for item_name, base_price in random.sample(template, random.randint(6, len(template))):
            menu_id += 1
            price = round(base_price * random.uniform(0.85, 1.2), 2)
            available = 1 if random.random() < 0.95 else 0
            restaurants[rid]["menu"].append((menu_id, price, available))
            t["MenuItems"].append((menu_id, rid, item_name, price, available))

    rest_by_city = {c: [r for r, v in restaurants.items() if v["city"] == c]
                    for c in CITIES}

    # ---- Couriers ----------------------------------------------------------------
    couriers = {}
    for cid, (city, founding) in enumerate(weighted_city_list(N_COURIERS), start=1):
        if founding or random.random() < 0.8:
            hired = START_DATE - timedelta(days=random.randint(30, 700))
        else:
            hired = START_DATE + \
                timedelta(days=random.randint(
                    0, (END_DATE - START_DATE).days - 60))
        couriers[cid] = {"city": city, "hired": hired,
                         "productivity": random.lognormvariate(0, 0.5)}
        t["Couriers"].append((cid, f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}", random_phone(),
                              city_ids[city], hired, 1 if random.random() < 0.9 else 0))
    courier_by_city = {c: [k for k, v in couriers.items() if v["city"] == c]
                       for c in CITIES}

    # ---- Customers and their order times ------------------------------------------
    reg_start = START_DATE - timedelta(days=540)
    reg_end = END_DATE - timedelta(days=15)
    reg_span = (reg_end - reg_start).days
    customers, order_plan = {}, []

    for cid in range(1, N_CUSTOMERS + 1):
        city = random.choices(list(CITIES), list(CITIES.values()))[0]
        first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
        # skewed to recent = growth
        reg_date = reg_start + \
            timedelta(days=int(reg_span * random.random() ** 0.7))
        registered_at = datetime.combine(reg_date, time(
            random.randint(8, 23), random.randint(0, 59), 0))

        lo = max(reg_date, START_DATE)
        churned = random.random() < 0.35
        hi = min(END_DATE, lo + timedelta(days=random.randint(30, 300))
                 ) if churned else END_DATE
        churned = hi < END_DATE

        rate = min(8, max(0.1, random.lognormvariate(0, 0.8))
                   )              # orders per month
        n_orders = poisson(rate * max(0.3, (hi - lo).days / 30))
        favorites = random.choices(rest_by_city[city], [
                                   restaurants[r]["popularity"] for r in rest_by_city[city]], k=3)
        customers[cid] = {"city": city, "favorites": favorites}

        t["Customers"].append((cid, f"{first} {last}", f"{first}.{last}{cid}@example.com".lower(),
                               random_phone(), city_ids[city], registered_at, 0 if churned else 1))

        times = sorted(random_dt(random_day(lo, hi)) for _ in range(n_orders))
        for i, dt in enumerate(times):
            order_plan.append({"dt": dt, "cust": cid, "first": i == 0})

    # ---- Orders, items, deliveries, reviews ----------------------------------------
    def pick_restaurant(cust, day):
        for _ in range(20):
            if random.random() < 0.65:
                rid = random.choice(cust["favorites"])
            else:
                pool = rest_by_city[cust["city"]]
                rid = random.choices(
                    pool, [restaurants[r]["popularity"] for r in pool])[0]
            if restaurants[rid]["joined"] <= day:
                return rid
        return min(rest_by_city[cust["city"]], key=lambda r: restaurants[r]["joined"])

    order_id = item_id = delivery_id = review_id = 0
    for plan in sorted(order_plan, key=lambda p: p["dt"]):
        order_id += 1
        dt, day = plan["dt"], plan["dt"].date()
        cust = customers[plan["cust"]]
        rid = pick_restaurant(cust, day)
        rest = restaurants[rid]

        available = [m for m in rest["menu"] if m[2]]
        chosen = random.sample(available, min(
            len(available), random.choices([1, 2, 3, 4, 5], [35, 35, 18, 8, 4])[0]))
        lines = [(m[0], random.choices([1, 2, 3], [75, 20, 5])[0], m[1])
                 for m in chosen]
        subtotal = sum(q * p for _, q, p in lines)

        distance = round(
            min(15, max(0.4, random.lognormvariate(math.log(3.0), 0.5))), 2)
        delivery_fee = round(1.0 + 0.45 * distance, 2)

        # promotion logic
        active = [p for p in t["Promotions"] if p[4]
                  <= day <= p[5] and p[1] != "WELCOME20"]
        promo_id, discount = None, 0.0
        if plan["first"] and random.random() < 0.7:
            promo_id = 1
        elif active and random.random() < 0.22:
            promo_id = random.choice(active)[0]
        if promo_id:
            _, _, dtype, value, _, _ = t["Promotions"][promo_id - 1]
            discount = round(subtotal * value / 100,
                             2) if dtype == "Percent" else float(value)
            discount = min(discount, round(subtotal, 2))

        cancelled = random.random() < 0.04
        t["Orders"].append((order_id, plan["cust"], rid, promo_id, dt,
                            "Cancelled" if cancelled else "Delivered",
                            random.choices(["Card", "Cash", "Wallet"], [
                                           55, 25, 20])[0],
                            delivery_fee, discount))
        for menu_item_id, qty, price in lines:
            item_id += 1
            t["OrderItems"].append(
                (item_id, order_id, menu_item_id, qty, price))

        if cancelled:
            continue

        pool = [c for c in courier_by_city[cust["city"]] if couriers[c]["hired"] <= day] \
            or courier_by_city[cust["city"]]
        courier = random.choices(
            pool, [couriers[c]["productivity"] for c in pool])[0]

        prep = random.randint(8, 25)
        if dt.hour in (12, 13, 19, 20, 21) and random.random() < 0.5:
            # kitchens are slower at peak hours
            prep += random.randint(5, 12)
        travel = distance * random.uniform(2.5, 4.5) + random.randint(2, 8)
        if random.random() < 0.05:
            # occasional big delay
            travel += random.randint(15, 40)
        picked_up = dt + timedelta(minutes=prep)
        delivered = picked_up + timedelta(seconds=int(travel * 60))
        delivery_id += 1
        t["Deliveries"].append(
            (delivery_id, order_id, courier, picked_up, delivered, distance))

        if random.random() < 0.45:
            total_minutes = (delivered - dt).total_seconds() / 60
            score = 4.5 - 0.6 * \
                max(0, (total_minutes - 40) / 15) + \
                rest["quality"] + random.gauss(0, 0.7)
            rating = int(min(5, max(1, round(score))))
            comment = random.choice(
                COMMENTS[rating]) if random.random() < 0.5 else None
            review_id += 1
            t["Reviews"].append((review_id, order_id, plan["cust"], rating, comment,
                                delivered + timedelta(minutes=random.randint(10, 2880))))
    return t


# ----------------------------------------------------------------------
# VALIDATION AND SUMMARY
# ----------------------------------------------------------------------
def validate(t):
    """Check the generated rows against the rules in the schema before touching the database."""
    orders = {o[0]: o for o in t["Orders"]}
    cust_city = {c[0]: c[4] for c in t["Customers"]}
    rest_city = {r[0]: r[3] for r in t["Restaurants"]}
    assert len({c[2] for c in t["Customers"]}) == len(
        t["Customers"]), "duplicate emails"
    assert all(m[3] > 0 for m in t["MenuItems"]), "non-positive menu price"
    assert len({(i[1], i[2]) for i in t["OrderItems"]}) == len(
        t["OrderItems"]), "duplicate order item"
    assert all(i[3] > 0 and i[4] > 0 for i in t["OrderItems"]
               ), "bad quantity or price"
    assert all(cust_city[o[1]] == rest_city[o[2]] for o in orders.values(
    )), "customer and restaurant in different cities"
    assert all(START_DATE <= o[4].date(
    ) <= END_DATE for o in orders.values()), "order date out of range"
    assert all(d[4] >= d[3] > orders[d[1]][4]
               for d in t["Deliveries"]), "delivery times out of order"
    assert len({d[1] for d in t["Deliveries"]}) == len(
        t["Deliveries"]), "two deliveries for one order"
    assert all(orders[d[1]][5] == "Delivered" for d in t["Deliveries"]
               ), "delivery for cancelled order"
    assert all(1 <= r[3] <= 5 for r in t["Reviews"]), "rating out of range"
    assert len({r[1] for r in t["Reviews"]}) == len(
        t["Reviews"]), "two reviews for one order"
    assert all(r[5] > orders[r[1]][4]
               for r in t["Reviews"]), "review before order"
    print("Validation passed: all rows respect the schema rules.")


def print_summary(t):
    print("\nRows generated:")
    for name, rows in t.items():
        print(f"  {name:<12}{len(rows):>8,}")
    revenue = sum(i[3] * i[4] for i in t["OrderItems"])
    delivered = [o for o in t["Orders"] if o[5] == "Delivered"]
    cancel_rate = 1 - len(delivered) / len(t["Orders"])
    avg_minutes = sum((d[4] - next(o[4] for o in [t["Orders"][d[1] - 1]])).total_seconds() / 60
                      for d in t["Deliveries"]) / len(t["Deliveries"])
    avg_rating = sum(r[3] for r in t["Reviews"]) / len(t["Reviews"])
    print(
        f"\nItem revenue: {revenue:,.0f} | avg order value: {revenue / len(t['Orders']):.2f}")
    print(
        f"Cancel rate: {cancel_rate:.1%} | avg delivery time: {avg_minutes:.1f} min | avg rating: {avg_rating:.2f}")


# ----------------------------------------------------------------------
# LOADING INTO SQL SERVER
# ----------------------------------------------------------------------
COLUMNS = {
    "Cities": ["CityID", "CityName"],
    "Cuisines": ["CuisineID", "CuisineName"],
    "Customers": ["CustomerID", "FullName", "Email", "Phone", "CityID", "RegisteredAt", "IsActive"],
    "Restaurants": ["RestaurantID", "RestaurantName", "CuisineID", "CityID", "JoinedAt", "IsActive"],
    "MenuItems": ["MenuItemID", "RestaurantID", "ItemName", "Price", "IsAvailable"],
    "Couriers": ["CourierID", "FullName", "Phone", "CityID", "HiredAt", "IsActive"],
    "Promotions": ["PromotionID", "PromoCode", "DiscountType", "DiscountValue", "StartDate", "EndDate"],
    "Orders": ["OrderID", "CustomerID", "RestaurantID", "PromotionID", "OrderDate", "OrderStatus",
               "PaymentMethod", "DeliveryFee", "DiscountAmount"],
    "OrderItems": ["OrderItemID", "OrderID", "MenuItemID", "Quantity", "UnitPrice"],
    "Deliveries": ["DeliveryID", "OrderID", "CourierID", "PickedUpAt", "DeliveredAt", "DistanceKm"],
    "Reviews": ["ReviewID", "OrderID", "CustomerID", "Rating", "Comment", "ReviewedAt"],
}
LOAD_ORDER = ["Cities", "Cuisines", "Customers", "Restaurants", "MenuItems", "Couriers", "Promotions",
              "Orders", "OrderItems", "Deliveries", "Reviews"]


def get_connection():
    import pyodbc
    drivers = [d for d in pyodbc.drivers() if "SQL Server" in d]
    if not drivers:
        raise SystemExit(
            "No SQL Server ODBC driver found. Install 'ODBC Driver 18 for SQL Server' from Microsoft.")
    modern = sorted(
        (d for d in drivers if d.startswith("ODBC Driver")), reverse=True)
    driver = modern[0] if modern else drivers[0]
    print(
        f"Connecting to {SERVER} / {DATABASE} using '{driver}' (Windows Authentication)...")
    conn_str = (f"DRIVER={{{driver}}};SERVER={SERVER};DATABASE={DATABASE};"
                "Trusted_Connection=yes;TrustServerCertificate=yes;")
    return pyodbc.connect(conn_str, autocommit=False)


def load_to_sql(t):
    conn = get_connection()
    cur = conn.cursor()
    cur.fast_executemany = True
    try:
        print("Clearing existing data...")
        for table in reversed(LOAD_ORDER):
            cur.execute(f"DELETE FROM dbo.{table}")
            cur.execute(
                f"DBCC CHECKIDENT ('dbo.{table}', RESEED, 0) WITH NO_INFOMSGS")

        for table in LOAD_ORDER:
            cols = COLUMNS[table]
            sql = f"INSERT INTO dbo.{table} ({', '.join(cols)}) VALUES ({', '.join(['?'] * len(cols))})"
            cur.execute(f"SET IDENTITY_INSERT dbo.{table} ON")
            rows = t[table]
            for i in range(0, len(rows), 5000):
                cur.executemany(sql, rows[i:i + 5000])
            cur.execute(f"SET IDENTITY_INSERT dbo.{table} OFF")
            print(f"  loaded {len(rows):>7,} rows into {table}")
        conn.commit()
        print("Done. Data committed.")
    except Exception:
        conn.rollback()
        print("Error - everything was rolled back, the database was not changed.")
        raise
    finally:
        conn.close()


# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate food delivery data and load it into SQL Server.")
    parser.add_argument("--dry-run", action="store_true",
                        help="generate and validate only, do not touch the database")
    args = parser.parse_args()

    random.seed(SEED)
    data = generate()
    validate(data)
    print_summary(data)
    if args.dry_run:
        print("\nDry run finished - nothing was written to the database.")
    else:
        load_to_sql(data)


if __name__ == "__main__":
    main()
