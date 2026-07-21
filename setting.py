import os
from pathlib import Path

from utils.env_config import env_int


BASE_DIR = Path(__file__).resolve().parent

# SQLite-only mode.
# Preferred file name follows the project convention requested by user.
SQLITE_DB_FILE = Path(
    os.getenv("SQLITE_DB_FILE", str(BASE_DIR / "data" / "customer_behaviour.db"))
)

# Local dashboard UI configuration.
DASHBOARD_CONFIG_LOCAL_FILE = BASE_DIR / "config" / "dashboard.yaml"

# Delay before showing the "session is going to be over soon" warning on dashboard.
SESSION_WARNING_DELAY_MINUTES = env_int("SESSION_WARNING_DELAY_MINUTES", 30)
