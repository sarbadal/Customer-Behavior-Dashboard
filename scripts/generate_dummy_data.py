from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


RANDOM_SEED = 42
ROWS = 1500
USER_COUNT = 420

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


def random_datetime(start: datetime, end: datetime) -> datetime:
    delta_seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, delta_seconds))


def write_browsing_history(users: list[str]) -> None:
    pages = [
        ("/home", "Landing"),
        ("/search", "Discovery"),
        ("/product/sku-100", "Product"),
        ("/product/sku-220", "Product"),
        ("/offers", "Promotion"),
        ("/cart", "Cart"),
        ("/support", "Support"),
        ("/blog/how-to-buy", "Content"),
        ("/checkout", "Checkout"),
    ]
    devices = ["Desktop", "Mobile", "Tablet"]
    referrers = ["Direct", "Google", "Instagram", "Email", "Affiliate", "YouTube"]

    path = DATA_DIR / "browsing_history.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "session_id",
                "user_id",
                "timestamp",
                "page_url",
                "category",
                "time_spent_seconds",
                "device",
                "referrer",
                "clicked_cta",
                "bounce",
            ]
        )

        start = datetime(2025, 1, 1)
        end = datetime(2026, 6, 30, 23, 59, 59)

        for i in range(ROWS):
            page_url, category = random.choice(pages)
            writer.writerow(
                [
                    f"S{i + 1:06d}",
                    random.choice(users),
                    random_datetime(start, end).isoformat(timespec="seconds"),
                    page_url,
                    category,
                    random.randint(10, 780),
                    random.choices(devices, weights=[40, 50, 10], k=1)[0],
                    random.choice(referrers),
                    random.choice(["Yes", "No"]),
                    random.choices(["Yes", "No"], weights=[20, 80], k=1)[0],
                ]
            )


def write_purchase_patterns(users: list[str]) -> None:
    catalog = {
        "Electronics": ["Smart Earbuds", "4K Monitor", "Mechanical Keyboard", "Wireless Mouse"],
        "Fashion": ["Denim Jacket", "Running Shoes", "Cotton Shirt", "Casual Sneakers"],
        "Groceries": ["Organic Coffee", "Almond Milk", "Protein Granola", "Olive Oil"],
        "Home": ["Desk Lamp", "Air Purifier", "Storage Basket", "Ceramic Set"],
        "Beauty": ["Face Serum", "Body Lotion", "Lip Tint", "Hair Mask"],
    }
    payments = ["Credit Card", "Debit Card", "UPI", "Wallet", "Net Banking", "Cash On Delivery"]

    path = DATA_DIR / "purchase_patterns.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "order_id",
                "user_id",
                "order_timestamp",
                "product_category",
                "product_name",
                "quantity",
                "unit_price",
                "discount_pct",
                "payment_method",
                "order_value",
                "is_returned",
            ]
        )

        start = datetime(2025, 1, 1)
        end = datetime(2026, 6, 30, 23, 59, 59)

        for i in range(ROWS):
            category = random.choice(list(catalog.keys()))
            product = random.choice(catalog[category])
            quantity = random.randint(1, 5)
            unit_price = round(random.uniform(8, 550), 2)
            discount_pct = random.choice([0, 5, 10, 15, 20, 25, 30])
            order_value = round(quantity * unit_price * (1 - discount_pct / 100), 2)

            writer.writerow(
                [
                    f"O{i + 1:06d}",
                    random.choice(users),
                    random_datetime(start, end).isoformat(timespec="seconds"),
                    category,
                    product,
                    quantity,
                    unit_price,
                    discount_pct,
                    random.choice(payments),
                    order_value,
                    random.choices(["Yes", "No"], weights=[7, 93], k=1)[0],
                ]
            )


def write_location_data(users: list[str]) -> None:
    locations = [
        ("India", "Bengaluru", "Karnataka", 12.9716, 77.5946),
        ("India", "Mumbai", "Maharashtra", 19.0760, 72.8777),
        ("India", "Delhi", "Delhi", 28.6139, 77.2090),
        ("India", "Pune", "Maharashtra", 18.5204, 73.8567),
        ("India", "Hyderabad", "Telangana", 17.3850, 78.4867),
        ("UAE", "Dubai", "Dubai", 25.2048, 55.2708),
        ("Singapore", "Singapore", "Singapore", 1.3521, 103.8198),
        ("UK", "London", "England", 51.5072, -0.1276),
        ("USA", "New York", "New York", 40.7128, -74.0060),
        ("Germany", "Berlin", "Berlin", 52.5200, 13.4050),
    ]
    traffic_sources = ["Organic", "Paid Search", "Social", "Email", "Referral", "Direct"]

    path = DATA_DIR / "location_data.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "event_id",
                "user_id",
                "event_timestamp",
                "country",
                "city",
                "region",
                "latitude",
                "longitude",
                "store_visit",
                "traffic_source",
            ]
        )

        start = datetime(2025, 1, 1)
        end = datetime(2026, 6, 30, 23, 59, 59)

        for i in range(ROWS):
            country, city, region, lat, lon = random.choice(locations)
            lat_jitter = round(lat + random.uniform(-0.05, 0.05), 6)
            lon_jitter = round(lon + random.uniform(-0.05, 0.05), 6)
            writer.writerow(
                [
                    f"E{i + 1:06d}",
                    random.choice(users),
                    random_datetime(start, end).isoformat(timespec="seconds"),
                    country,
                    city,
                    region,
                    lat_jitter,
                    lon_jitter,
                    random.choices(["Yes", "No"], weights=[25, 75], k=1)[0],
                    random.choice(traffic_sources),
                ]
            )


def main() -> None:
    random.seed(RANDOM_SEED)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    users = [f"U{i:05d}" for i in range(1, USER_COUNT + 1)]

    write_browsing_history(users)
    write_purchase_patterns(users)
    write_location_data(users)

    print(f"Created dummy CSV files in: {DATA_DIR}")


if __name__ == "__main__":
    main()
