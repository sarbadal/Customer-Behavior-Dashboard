import os
from pathlib import Path
from typing import Literal

from utils.env_config import env_bool, env_int


BASE_DIR = Path(__file__).resolve().parent

# Choose one: "sqlite", "mysql", "local", or "gcp_bucket"
DATA_SOURCE: Literal["sqlite", "mysql", "local", "gcp_bucket"] = os.getenv("DATA_SOURCE", "sqlite").strip().lower()  # type: ignore[assignment]

# SQLite database path (used when DATA_SOURCE="sqlite")
SQLITE_DB_FILE = Path(os.getenv("SQLITE_DB_FILE", str(BASE_DIR / "data" / "customer_behavior.db")))

# MySQL settings (used when DATA_SOURCE="mysql")
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1").strip()
MYSQL_PORT = env_int("MYSQL_PORT", 3306)
MYSQL_USER = os.getenv("MYSQL_USER", "root").strip()
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "").strip()
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "customer_behavior").strip()
MYSQL_SSL_CA = os.getenv("MYSQL_SSL_CA", "").strip()
MYSQL_TABLE_BROWSING_HISTORY = os.getenv("MYSQL_TABLE_BROWSING_HISTORY", "browsing_history").strip()
MYSQL_TABLE_PURCHASE_PATTERNS = os.getenv("MYSQL_TABLE_PURCHASE_PATTERNS", "purchase_patterns").strip()
MYSQL_TABLE_LOCATION_DATA = os.getenv("MYSQL_TABLE_LOCATION_DATA", "location_data").strip()
DB_AUTO_BOOTSTRAP_FROM_SQLITE = env_bool("DB_AUTO_BOOTSTRAP_FROM_SQLITE", default=True)

# gs://customer-behavior-dashboard/data/browsing_history.csv

# Local CSV folder path (used when DATA_SOURCE="local")
LOCAL_DATA_DIR = BASE_DIR / "data"

# GCP bucket settings (used when DATA_SOURCE="gcp_bucket")
GCP_PROJECT_ID = "development-490607"
GCP_BUCKET_NAME = "customer-behavior-dashboard"
GCP_BUCKET_DATA_PREFIX = "data"

# Set to False when deployed in the same GCP project (e.g., Cloud Functions/Cloud Run)
# so Application Default Credentials are used instead of a JSON key file.
GCP_USE_JSON_KEY = env_bool("GCP_USE_JSON_KEY", default=True)
GCP_CREDENTIALS_FILE = BASE_DIR / "gcp" / "cred_key.json"

# Dashboard YAML config source
# - local: read from DASHBOARD_CONFIG_LOCAL_FILE
# - gcp_bucket: read from GCS object (bucket can be dedicated, static, or data bucket)
DASHBOARD_CONFIG_SOURCE: Literal["local", "gcp_bucket"] = os.getenv("DASHBOARD_CONFIG_SOURCE", "local").strip().lower()  # type: ignore[assignment]
DASHBOARD_CONFIG_LOCAL_FILE = BASE_DIR / "config" / "dashboard.yaml"

# Optional dedicated config bucket/object for dashboard YAML.
# If bucket is empty and DASHBOARD_CONFIG_SOURCE='gcp_bucket', code falls back to:
# 1) GCS_STATIC_BUCKET (if set)
# 2) GCP_BUCKET_NAME
DASHBOARD_CONFIG_GCS_BUCKET = os.getenv("DASHBOARD_CONFIG_GCS_BUCKET", "").strip()
DASHBOARD_CONFIG_GCS_OBJECT = os.getenv("DASHBOARD_CONFIG_GCS_OBJECT", "config/dashboard.yaml").strip("/")

# Optional GCS auth/project overrides specifically for dashboard config reads.
DASHBOARD_CONFIG_GCS_PROJECT_ID = os.getenv("DASHBOARD_CONFIG_GCS_PROJECT_ID", GCP_PROJECT_ID).strip()
DASHBOARD_CONFIG_GCS_USE_JSON_KEY = env_bool("DASHBOARD_CONFIG_GCS_USE_JSON_KEY", default=GCP_USE_JSON_KEY)
DASHBOARD_CONFIG_GCS_CREDENTIALS_FILE = Path(
	os.getenv("DASHBOARD_CONFIG_GCS_CREDENTIALS_FILE", str(GCP_CREDENTIALS_FILE))
)
