from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import setting

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError:  # pragma: no cover - optional unless mysql mode is selected
    pymysql = None
    DictCursor = None


_DATASET_TO_TABLE = {
    "browsing_history.csv": "browsing_history",
    "purchase_patterns.csv": "purchase_patterns",
    "location_data.csv": "location_data",
}


def _validate_table_name(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise RuntimeError(f"Unsafe SQL table name configured: {name}")
    return name


def _mysql_table_mapping() -> dict[str, str]:
    return {
        "browsing_history.csv": _validate_table_name(setting.MYSQL_TABLE_BROWSING_HISTORY),
        "purchase_patterns.csv": _validate_table_name(setting.MYSQL_TABLE_PURCHASE_PATTERNS),
        "location_data.csv": _validate_table_name(setting.MYSQL_TABLE_LOCATION_DATA),
    }


def _resolve_sqlite_db_file() -> Path:
    return Path(setting.SQLITE_DB_FILE)


def _table_name_from_csv_filename(csv_name: str) -> str:
    if setting.DATA_SOURCE == "mysql":
        table_name = _mysql_table_mapping().get(csv_name)
    else:
        table_name = _DATASET_TO_TABLE.get(csv_name)

    if not table_name:
        raise RuntimeError(f"No SQL table mapping found for dataset: {csv_name}")
    return table_name


def _read_sqlite_rows(db_file: Path, table_name: str) -> list[dict[str, str]]:
    if not db_file.exists():
        raise RuntimeError(f"SQLite database file not found: {db_file}")

    with sqlite3.connect(db_file) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(f"SELECT * FROM {table_name}")
        return [dict(row) for row in cursor.fetchall()]


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
        "autocommit": True,
        "connect_timeout": int(setting.MYSQL_CONNECT_TIMEOUT),
        "read_timeout": int(setting.MYSQL_READ_TIMEOUT),
        "write_timeout": int(setting.MYSQL_WRITE_TIMEOUT),
        "cursorclass": DictCursor,
    }

    if setting.MYSQL_SSL_CA:
        ssl_ca_path = Path(setting.MYSQL_SSL_CA)
        if ssl_ca_path.is_file():
            connect_kwargs["ssl"] = {"ca": str(ssl_ca_path)}

    return pymysql.connect(**connect_kwargs)


def _read_mysql_rows(table_name: str) -> list[dict[str, str]]:
    conn = _mysql_connect()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM `{table_name}`")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    table_name = _table_name_from_csv_filename(path.name)
    if setting.DATA_SOURCE == "mysql":
        return _read_mysql_rows(table_name=table_name)

    if setting.DATA_SOURCE != "sqlite":
        raise RuntimeError("Unsupported DATA_SOURCE. Use 'sqlite' or 'mysql'.")

    db_file = _resolve_sqlite_db_file()
    return _read_sqlite_rows(db_file=db_file, table_name=table_name)


def check_data_source_health() -> tuple[bool, dict[str, object]]:
    """Validate that the configured database source is reachable and has required tables."""

    required_datasets = [
        "browsing_history.csv",
        "purchase_patterns.csv",
        "location_data.csv",
    ]

    if setting.DATA_SOURCE == "mysql":
        details: dict[str, object] = {
            "data_source": "mysql",
            "host": setting.MYSQL_HOST,
            "port": int(setting.MYSQL_PORT),
            "database": setting.MYSQL_DATABASE,
            "user": setting.MYSQL_USER,
        }
        required_tables = [_table_name_from_csv_filename(name) for name in required_datasets]
        try:
            conn = _mysql_connect()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    for table_name in required_tables:
                        cursor.execute("SHOW TABLES LIKE %s", (table_name,))
                        if cursor.fetchone() is None:
                            return False, {**details, "message": f"Missing MySQL table: {table_name}"}
            finally:
                conn.close()
            return True, {**details, "message": "MySQL connection is healthy."}
        except Exception as exc:  # pragma: no cover
            return False, {**details, "message": f"MySQL health check failed: {exc}"}

    if setting.DATA_SOURCE != "sqlite":
        return False, {
            "data_source": setting.DATA_SOURCE,
            "message": "Unsupported DATA_SOURCE. Use 'sqlite' or 'mysql'.",
        }

    db_file = _resolve_sqlite_db_file()
    details = {
        "data_source": "sqlite",
        "database_file": str(db_file),
    }

    if not db_file.exists():
        return False, {**details, "message": f"SQLite database file not found: {db_file}"}

    required_tables = [_table_name_from_csv_filename(name) for name in required_datasets]

    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            for table_name in required_tables:
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,),
                )
                if cursor.fetchone() is None:
                    return False, {**details, "message": f"Missing SQLite table: {table_name}"}
        return True, {**details, "message": "SQLite connection is healthy."}
    except Exception as exc:  # pragma: no cover
        return False, {**details, "message": f"SQLite health check failed: {exc}"}


def check_runtime_db_ready() -> tuple[bool, dict[str, object]]:
    """Check runtime DB readiness used by wake-status (connection-level, not schema-level)."""

    if setting.DATA_SOURCE == "mysql":
        details: dict[str, object] = {
            "data_source": "mysql",
            "host": setting.MYSQL_HOST,
            "port": int(setting.MYSQL_PORT),
            "database": setting.MYSQL_DATABASE,
            "user": setting.MYSQL_USER,
        }
        try:
            conn = _mysql_connect()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
            finally:
                conn.close()
            return True, {**details, "message": "MySQL runtime connection is ready."}
        except Exception as exc:  # pragma: no cover
            return False, {**details, "message": f"MySQL runtime connection check failed: {exc}"}

    if setting.DATA_SOURCE == "sqlite":
        db_file = _resolve_sqlite_db_file()
        details = {
            "data_source": "sqlite",
            "database_file": str(db_file),
        }
        if not db_file.exists():
            return False, {**details, "message": f"SQLite database file not found: {db_file}"}
        try:
            with sqlite3.connect(db_file) as conn:
                conn.execute("SELECT 1")
            return True, {**details, "message": "SQLite runtime connection is ready."}
        except Exception as exc:  # pragma: no cover
            return False, {**details, "message": f"SQLite runtime connection check failed: {exc}"}

    return False, {
        "data_source": setting.DATA_SOURCE,
        "message": "Unsupported DATA_SOURCE. Use 'sqlite' or 'mysql'.",
    }
