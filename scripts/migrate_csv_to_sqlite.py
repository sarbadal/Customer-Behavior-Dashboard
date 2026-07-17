import csv
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_FILE = DATA_DIR / "customer_behavior.db"


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS browsing_history (
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            category TEXT NOT NULL,
            device TEXT NOT NULL,
            time_spent_seconds INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS purchase_patterns (
            user_id TEXT NOT NULL,
            order_id TEXT NOT NULL,
            order_timestamp TEXT NOT NULL,
            order_value REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS location_data (
            user_id TEXT NOT NULL,
            event_timestamp TEXT NOT NULL,
            city TEXT NOT NULL,
            region TEXT NOT NULL,
            traffic_source TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_browsing_user ON browsing_history(user_id);
        CREATE INDEX IF NOT EXISTS idx_purchase_user ON purchase_patterns(user_id);
        CREATE INDEX IF NOT EXISTS idx_location_user ON location_data(user_id);
        CREATE INDEX IF NOT EXISTS idx_purchase_timestamp ON purchase_patterns(order_timestamp);
        CREATE INDEX IF NOT EXISTS idx_location_region ON location_data(region);
        """
    )


def _replace_table_rows(conn: sqlite3.Connection, table_name: str, columns: list[str], rows: list[dict[str, str]]) -> int:
    conn.execute(f"DELETE FROM {table_name}")

    if not rows:
        return 0

    placeholders = ", ".join("?" for _ in columns)
    column_list = ", ".join(columns)
    sql = f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})"

    values = [tuple(row.get(column, "") for column in columns) for row in rows]
    conn.executemany(sql, values)
    return len(values)


def migrate() -> None:
    browsing_rows = _read_csv(DATA_DIR / "browsing_history.csv")
    purchase_rows = _read_csv(DATA_DIR / "purchase_patterns.csv")
    location_rows = _read_csv(DATA_DIR / "location_data.csv")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_FILE) as conn:
        _create_schema(conn)

        browsing_count = _replace_table_rows(
            conn,
            "browsing_history",
            ["user_id", "session_id", "timestamp", "category", "device", "time_spent_seconds"],
            browsing_rows,
        )
        purchase_count = _replace_table_rows(
            conn,
            "purchase_patterns",
            ["user_id", "order_id", "order_timestamp", "order_value"],
            purchase_rows,
        )
        location_count = _replace_table_rows(
            conn,
            "location_data",
            ["user_id", "event_timestamp", "city", "region", "traffic_source"],
            location_rows,
        )

        conn.commit()

    print(f"SQLite database updated: {DB_FILE}")
    print(f"browsing_history rows: {browsing_count}")
    print(f"purchase_patterns rows: {purchase_count}")
    print(f"location_data rows: {location_count}")


if __name__ == "__main__":
    migrate()
