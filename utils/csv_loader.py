from __future__ import annotations

import sqlite3
from pathlib import Path

import setting


_DATASET_TO_TABLE = {
    "browsing_history.csv": "browsing_history",
    "purchase_patterns.csv": "purchase_patterns",
    "location_data.csv": "location_data",
}


def _resolve_sqlite_db_file() -> Path:
    return Path(setting.SQLITE_DB_FILE)


def _table_name_from_csv_filename(csv_name: str) -> str:
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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    db_file = _resolve_sqlite_db_file()
    table_name = _table_name_from_csv_filename(path.name)
    return _read_sqlite_rows(db_file=db_file, table_name=table_name)


def check_data_source_health() -> tuple[bool, dict[str, object]]:
    """Validate that the SQLite database is reachable and has required tables."""

    db_file = _resolve_sqlite_db_file()
    details: dict[str, object] = {
        "data_source": "sqlite",
        "database_file": str(db_file),
    }

    if not db_file.exists():
        return False, {**details, "message": f"SQLite database file not found: {db_file}"}

    required_tables = [
        _table_name_from_csv_filename("browsing_history.csv"),
        _table_name_from_csv_filename("purchase_patterns.csv"),
        _table_name_from_csv_filename("location_data.csv"),
    ]

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
