from pathlib import Path
from typing import Literal

from utils.env_config import env_bool


BASE_DIR = Path(__file__).resolve().parent

# Choose one: "local" or "gcp_bucket"
DATA_SOURCE: Literal["local", "gcp_bucket"] = "local"

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
