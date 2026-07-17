from __future__ import annotations

import csv
import io
import re
import sqlite3
from pathlib import Path

import setting

try:
    from google.cloud import storage
except ImportError:  # pragma: no cover - dependency is optional outside prod bucket mode
    storage = None

try:
    from google.oauth2 import service_account
except ImportError:  # pragma: no cover - only required when JSON key mode is enabled
    service_account = None

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError:  # pragma: no cover - dependency is optional unless mysql mode is used
    pymysql = None
    DictCursor = None


def _read_local_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def _read_sqlite_rows(db_file: Path, table_name: str) -> list[dict[str, str]]:
    if not db_file.exists():
        raise RuntimeError(f"SQLite database file not found: {db_file}")

    with sqlite3.connect(db_file) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(f"SELECT * FROM {table_name}")
        return [dict(row) for row in cursor.fetchall()]


def _table_name_from_csv_filename(csv_name: str, data_source: str) -> str:
    if data_source == "mysql":
        mapping = {
            "browsing_history.csv": setting.MYSQL_TABLE_BROWSING_HISTORY,
            "purchase_patterns.csv": setting.MYSQL_TABLE_PURCHASE_PATTERNS,
            "location_data.csv": setting.MYSQL_TABLE_LOCATION_DATA,
        }
    else:
        mapping = {
            "browsing_history.csv": "browsing_history",
            "purchase_patterns.csv": "purchase_patterns",
            "location_data.csv": "location_data",
        }

    if csv_name not in mapping:
        raise RuntimeError(f"No SQL table mapping found for dataset: {csv_name}")

    table_name = mapping[csv_name]
    if not re.fullmatch(r"[A-Za-z0-9_]+", table_name):
        raise RuntimeError(f"Unsafe SQL table name configured: {table_name}")
    return table_name


def _read_mysql_rows(table_name: str) -> list[dict[str, str]]:
    if pymysql is None or DictCursor is None:
        raise RuntimeError("PyMySQL is required for mysql data mode. Install dependencies first.")

    connect_kwargs: dict[str, object] = {
        "host": setting.MYSQL_HOST,
        "port": int(setting.MYSQL_PORT),
        "user": setting.MYSQL_USER,
        "password": setting.MYSQL_PASSWORD,
        "database": setting.MYSQL_DATABASE,
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "autocommit": True,
    }

    if setting.MYSQL_SSL_CA:
        connect_kwargs["ssl"] = {"ca": setting.MYSQL_SSL_CA}

    conn = pymysql.connect(**connect_kwargs)
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM `{table_name}`")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()


def _create_gcs_client(project_id: str | None, use_json_key: bool, credentials_file: Path) -> "storage.Client":
    if storage is None:
        raise RuntimeError(
            "google-cloud-storage is required for bucket data mode. Install dependencies in production."
        )

    if not use_json_key:
        # Use Application Default Credentials (recommended for Cloud Functions/Cloud Run in same project).
        return storage.Client(project=project_id or None)

    if service_account is None:
        raise RuntimeError("google-auth is required for JSON key mode.")

    if not credentials_file.exists():
        raise RuntimeError(f"GCP credentials file not found: {credentials_file}")

    credentials = service_account.Credentials.from_service_account_file(str(credentials_file))
    return storage.Client(project=project_id or None, credentials=credentials)


def _read_gcs_csv_rows(client: "storage.Client", bucket: str, blob_name: str) -> list[dict[str, str]]:
    if storage is None:
        raise RuntimeError(
            "google-cloud-storage is required for bucket data mode. Install dependencies in production."
        )

    gcs_bucket = client.bucket(bucket)
    blob = gcs_bucket.blob(blob_name)
    csv_text = blob.download_as_text(encoding="utf-8")
    return list(csv.DictReader(io.StringIO(csv_text)))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    data_source = setting.DATA_SOURCE.strip().lower()

    # Keep backward compatibility with older env values.
    if data_source == "bucket":
        data_source = "gcp_bucket"

    if data_source == "local":
        local_data_dir = Path(setting.LOCAL_DATA_DIR)
        return _read_local_csv_rows(local_data_dir / path.name)

    if data_source == "sqlite":
        db_file = Path(setting.SQLITE_DB_FILE)
        table_name = _table_name_from_csv_filename(path.name, data_source="sqlite")
        return _read_sqlite_rows(db_file=db_file, table_name=table_name)

    if data_source == "mysql":
        table_name = _table_name_from_csv_filename(path.name, data_source="mysql")
        return _read_mysql_rows(table_name=table_name)

    if data_source != "gcp_bucket":
        raise RuntimeError("Invalid DATA_SOURCE in setting.py. Use 'sqlite', 'mysql', 'local', or 'gcp_bucket'.")

    bucket = str(setting.GCP_BUCKET_NAME).strip()
    data_prefix = str(setting.GCP_BUCKET_DATA_PREFIX).strip("/")
    gcp_project_id = str(setting.GCP_PROJECT_ID).strip() or None
    use_json_key = bool(setting.GCP_USE_JSON_KEY)
    credentials_file = Path(setting.GCP_CREDENTIALS_FILE)

    if not bucket:
        raise RuntimeError("GCP_BUCKET_NAME is required in setting.py when DATA_SOURCE='gcp_bucket'.")

    blob_name = f"{data_prefix}/{path.name}" if data_prefix else path.name
    gcs_client = _create_gcs_client(
        project_id=gcp_project_id,
        use_json_key=use_json_key,
        credentials_file=credentials_file,
    )
    return _read_gcs_csv_rows(client=gcs_client, bucket=bucket, blob_name=blob_name)


def check_data_source_health() -> tuple[bool, dict[str, object]]:
    """Validate that the configured data source is reachable and minimally queryable."""

    data_source = setting.DATA_SOURCE.strip().lower()
    if data_source == "bucket":
        data_source = "gcp_bucket"

    details: dict[str, object] = {"data_source": data_source}

    if data_source == "sqlite":
        db_file = Path(setting.SQLITE_DB_FILE)
        details["database_file"] = str(db_file)
        if not db_file.exists():
            return False, {**details, "message": f"SQLite database file not found: {db_file}"}

        try:
            with sqlite3.connect(db_file) as conn:
                cursor = conn.cursor()
                required_tables = [
                    _table_name_from_csv_filename("browsing_history.csv", data_source="sqlite"),
                    _table_name_from_csv_filename("purchase_patterns.csv", data_source="sqlite"),
                    _table_name_from_csv_filename("location_data.csv", data_source="sqlite"),
                ]
                for table_name in required_tables:
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                        (table_name,),
                    )
                    if cursor.fetchone() is None:
                        return False, {**details, "message": f"Missing SQLite table: {table_name}"}
            return True, {**details, "message": "SQLite connection is healthy."}
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            return False, {**details, "message": f"SQLite health check failed: {exc}"}

    if data_source == "mysql":
        details.update(
            {
                "host": setting.MYSQL_HOST,
                "port": int(setting.MYSQL_PORT),
                "database": setting.MYSQL_DATABASE,
                "user": setting.MYSQL_USER,
            }
        )

        try:
            required_tables = [
                _table_name_from_csv_filename("browsing_history.csv", data_source="mysql"),
                _table_name_from_csv_filename("purchase_patterns.csv", data_source="mysql"),
                _table_name_from_csv_filename("location_data.csv", data_source="mysql"),
            ]
            if pymysql is None or DictCursor is None:
                return False, {**details, "message": "PyMySQL is required for mysql data mode."}

            connect_kwargs: dict[str, object] = {
                "host": setting.MYSQL_HOST,
                "port": int(setting.MYSQL_PORT),
                "user": setting.MYSQL_USER,
                "password": setting.MYSQL_PASSWORD,
                "database": setting.MYSQL_DATABASE,
                "charset": "utf8mb4",
                "cursorclass": DictCursor,
                "autocommit": True,
            }
            if setting.MYSQL_SSL_CA:
                connect_kwargs["ssl"] = {"ca": setting.MYSQL_SSL_CA}

            conn = pymysql.connect(**connect_kwargs)
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
        except Exception as exc:  # pragma: no cover - depends on deployment infra
            return False, {**details, "message": f"MySQL health check failed: {exc}"}

    if data_source == "local":
        local_data_dir = Path(setting.LOCAL_DATA_DIR)
        details["data_directory"] = str(local_data_dir)
        required = ["browsing_history.csv", "purchase_patterns.csv", "location_data.csv"]
        missing = [name for name in required if not (local_data_dir / name).exists()]
        if missing:
            return False, {**details, "message": f"Missing local data files: {', '.join(missing)}"}
        return True, {**details, "message": "Local data source is healthy."}

    if data_source == "gcp_bucket":
        bucket = str(setting.GCP_BUCKET_NAME).strip()
        data_prefix = str(setting.GCP_BUCKET_DATA_PREFIX).strip("/")
        details["bucket"] = bucket
        details["prefix"] = data_prefix
        if not bucket:
            return False, {**details, "message": "GCP_BUCKET_NAME is required for gcp_bucket mode."}

        try:
            gcs_client = _create_gcs_client(
                project_id=str(setting.GCP_PROJECT_ID).strip() or None,
                use_json_key=bool(setting.GCP_USE_JSON_KEY),
                credentials_file=Path(setting.GCP_CREDENTIALS_FILE),
            )
            gcs_bucket = gcs_client.bucket(bucket)
            required = ["browsing_history.csv", "purchase_patterns.csv", "location_data.csv"]
            for name in required:
                blob_name = f"{data_prefix}/{name}" if data_prefix else name
                if not gcs_bucket.blob(blob_name).exists(client=gcs_client):
                    return False, {**details, "message": f"Missing GCS object: {blob_name}"}
            return True, {**details, "message": "GCP bucket data source is healthy."}
        except Exception as exc:  # pragma: no cover - depends on cloud environment
            return False, {**details, "message": f"GCP bucket health check failed: {exc}"}

    return False, {**details, "message": "Unsupported DATA_SOURCE. Use sqlite/mysql/local/gcp_bucket."}
