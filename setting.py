import os
from pathlib import Path
from typing import Literal

from utils.env_config import env_int


BASE_DIR = Path(__file__).resolve().parent

# Select runtime database backend: "sqlite" or "mysql".
DATA_SOURCE: Literal["sqlite", "mysql"] = os.getenv("DATA_SOURCE", "sqlite").strip().lower()  # type: ignore[assignment]

# SQLite-only mode.
# Preferred file name follows the project convention requested by user.
SQLITE_DB_FILE = Path(
    os.getenv("SQLITE_DB_FILE", str(BASE_DIR / "data" / "customer_behaviour.db"))
)

# MySQL settings (used when DATA_SOURCE="mysql").
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1").strip()
MYSQL_PORT = env_int("MYSQL_PORT", 3306)
MYSQL_USER = os.getenv("MYSQL_USER", "root").strip()
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "").strip()
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "customer_behavior").strip()
MYSQL_SSL_CA = os.getenv("MYSQL_SSL_CA", "").strip()
MYSQL_CONNECT_TIMEOUT = env_int("MYSQL_CONNECT_TIMEOUT", 8)
MYSQL_READ_TIMEOUT = env_int("MYSQL_READ_TIMEOUT", 15)
MYSQL_WRITE_TIMEOUT = env_int("MYSQL_WRITE_TIMEOUT", 15)
MYSQL_TABLE_BROWSING_HISTORY = os.getenv("MYSQL_TABLE_BROWSING_HISTORY", "browsing_history").strip()
MYSQL_TABLE_PURCHASE_PATTERNS = os.getenv("MYSQL_TABLE_PURCHASE_PATTERNS", "purchase_patterns").strip()
MYSQL_TABLE_LOCATION_DATA = os.getenv("MYSQL_TABLE_LOCATION_DATA", "location_data").strip()

# Local dashboard UI configuration.
DASHBOARD_CONFIG_LOCAL_FILE = BASE_DIR / "config" / "dashboard.yaml"

# Delay before showing the "session is going to be over soon" warning on dashboard.
SESSION_WARNING_DELAY_MINUTES = env_int("SESSION_WARNING_DELAY_MINUTES", 30)
