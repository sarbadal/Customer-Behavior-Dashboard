from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import setting

try:
    import pymysql
except ImportError:  # pragma: no cover - optional unless mysql mode is used
    pymysql = None


_SQLITE_TABLES = [
    "browsing_history",
    "purchase_patterns",
    "location_data",
]


def _validate_table_name(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise RuntimeError(f"Unsafe SQL table name configured: {name}")
    return name


def _mysql_table_mapping() -> dict[str, str]:
    return {
        "browsing_history": _validate_table_name(setting.MYSQL_TABLE_BROWSING_HISTORY),
        "purchase_patterns": _validate_table_name(setting.MYSQL_TABLE_PURCHASE_PATTERNS),
        "location_data": _validate_table_name(setting.MYSQL_TABLE_LOCATION_DATA),
    }


def _mysql_connect() -> "pymysql.connections.Connection":
    if pymysql is None:
        raise RuntimeError("PyMySQL is required for mysql data mode. Install dependencies first.")

    connect_kwargs: dict[str, object] = {
        "host": setting.MYSQL_HOST,
        "port": int(setting.MYSQL_PORT),
        "user": setting.MYSQL_USER,
        "password": setting.MYSQL_PASSWORD,
        "database": setting.MYSQL_DATABASE,
        "charset": "utf8mb4",
        "autocommit": False,
        "connect_timeout": int(setting.MYSQL_CONNECT_TIMEOUT),
        "read_timeout": int(setting.MYSQL_READ_TIMEOUT),
        "write_timeout": int(setting.MYSQL_WRITE_TIMEOUT),
    }

    if setting.MYSQL_SSL_CA:
        connect_kwargs["ssl"] = {"ca": setting.MYSQL_SSL_CA}

    return pymysql.connect(**connect_kwargs)


def _mysql_table_exists(conn: "pymysql.connections.Connection", table_name: str) -> bool:
    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES LIKE %s", (table_name,))
        return cursor.fetchone() is not None


def _create_mysql_table_if_missing(conn: "pymysql.connections.Connection", table_name: str, sqlite_name: str) -> None:
    create_sql_by_table = {
        "browsing_history": f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                user_id VARCHAR(128) NOT NULL,
                session_id VARCHAR(128) NOT NULL,
                timestamp DATETIME NOT NULL,
                category VARCHAR(128) NOT NULL,
                device VARCHAR(64) NOT NULL,
                time_spent_seconds INT NOT NULL,
                INDEX idx_{table_name}_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        "purchase_patterns": f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                user_id VARCHAR(128) NOT NULL,
                order_id VARCHAR(128) NOT NULL,
                order_timestamp DATETIME NOT NULL,
                order_value DECIMAL(12,2) NOT NULL,
                INDEX idx_{table_name}_user (user_id),
                INDEX idx_{table_name}_ts (order_timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        "location_data": f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                user_id VARCHAR(128) NOT NULL,
                event_timestamp DATETIME NOT NULL,
                city VARCHAR(128) NOT NULL,
                region VARCHAR(128) NOT NULL,
                traffic_source VARCHAR(128) NOT NULL,
                INDEX idx_{table_name}_user (user_id),
                INDEX idx_{table_name}_region (region)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
    }

    sql = create_sql_by_table.get(sqlite_name)
    if not sql:
        raise RuntimeError(f"No schema mapping found for table: {sqlite_name}")

    with conn.cursor() as cursor:
        cursor.execute(sql)


def _read_sqlite_rows(sqlite_db_file: Path, table_name: str) -> list[tuple[object, ...]]:
    if not sqlite_db_file.exists():
        raise RuntimeError(f"Local SQLite database file not found: {sqlite_db_file}")

    with sqlite3.connect(sqlite_db_file) as conn:
        cursor = conn.execute(f"SELECT * FROM {table_name}")
        return cursor.fetchall()


def _insert_rows_into_mysql(
    conn: "pymysql.connections.Connection",
    mysql_table_name: str,
    sqlite_table_name: str,
    rows: list[tuple[object, ...]],
) -> int:
    if not rows:
        return 0

    columns_by_table = {
        "browsing_history": [
            "user_id",
            "session_id",
            "timestamp",
            "category",
            "device",
            "time_spent_seconds",
        ],
        "purchase_patterns": [
            "user_id",
            "order_id",
            "order_timestamp",
            "order_value",
        ],
        "location_data": [
            "user_id",
            "event_timestamp",
            "city",
            "region",
            "traffic_source",
        ],
    }

    columns = columns_by_table[sqlite_table_name]
    placeholders = ", ".join(["%s"] * len(columns))
    column_list = ", ".join([f"`{column}`" for column in columns])
    sql = f"INSERT INTO `{mysql_table_name}` ({column_list}) VALUES ({placeholders})"

    with conn.cursor() as cursor:
        cursor.executemany(sql, rows)

    return len(rows)


def bootstrap_mysql_from_local_sqlite_if_needed() -> dict[str, object]:
    """Create missing MySQL tables and seed them from the local SQLite database."""

    if setting.DATA_SOURCE.strip().lower() != "mysql":
        return {
            "status": "skipped",
            "message": "Bootstrap skipped: DATA_SOURCE is not mysql.",
        }

    sqlite_db_file = Path(setting.SQLITE_DB_FILE)
    table_mapping = _mysql_table_mapping()

    conn = _mysql_connect()
    try:
        created_tables: list[str] = []
        seeded_rows: dict[str, int] = {}

        for sqlite_table in _SQLITE_TABLES:
            mysql_table = table_mapping[sqlite_table]
            if _mysql_table_exists(conn, mysql_table):
                continue

            _create_mysql_table_if_missing(conn, mysql_table, sqlite_table)
            created_tables.append(mysql_table)

            sqlite_rows = _read_sqlite_rows(sqlite_db_file, sqlite_table)
            row_count = _insert_rows_into_mysql(conn, mysql_table, sqlite_table, sqlite_rows)
            seeded_rows[mysql_table] = row_count

        conn.commit()

        if not created_tables:
            return {
                "status": "ok",
                "message": "MySQL tables already exist. No bootstrap needed.",
                "created_tables": [],
                "seeded_rows": {},
            }

        return {
            "status": "ok",
            "message": "MySQL bootstrap completed from local SQLite.",
            "sqlite_source": str(sqlite_db_file),
            "created_tables": created_tables,
            "seeded_rows": seeded_rows,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
