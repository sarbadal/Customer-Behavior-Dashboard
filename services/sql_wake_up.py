import os
import logging
from datetime import datetime, timezone
from typing import Any
from pathlib import Path

import setting
from services.wake_sql_client import WakeSqlFunctionClient

try:
    from google.cloud import firestore
    from google.cloud.exceptions import GoogleCloudError
    from google.oauth2 import service_account
except ImportError:  # Firestore is optional for local/dev runs.
    firestore = None
    GoogleCloudError = Exception
    service_account = None

logger = logging.getLogger(__name__)

FIRESTORE_DATABASE_ID = os.getenv("FIRESTORE_DATABASE_ID", "(default)")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOCAL_FIRESTORE_CREDENTIALS = PROJECT_ROOT / "gcp" / "cred_key.json"


def _running_in_google_cloud_functions() -> bool:
    """Detect Google Cloud Functions/Cloud Run managed runtime."""
    cloud_markers = (
        "K_SERVICE",
        "FUNCTION_TARGET",
        "FUNCTION_NAME",
        "X_GOOGLE_FUNCTION_NAME",
    )
    return any(os.getenv(marker) for marker in cloud_markers)


def _get_firestore_client() -> Any | None:
    """Create a Firestore client when credentials/environment are available."""
    if firestore is None:
        logger.warning("google-cloud-firestore is not installed; skipping Firestore activity tracking.")
        return None

    try:
        if _running_in_google_cloud_functions():
            return firestore.Client(database=FIRESTORE_DATABASE_ID)

        if service_account is None:
            logger.warning("google-auth is not installed; cannot load local Firestore credentials.")
            return None

        credentials_path = Path(
            os.getenv("FIRESTORE_CREDENTIALS_FILE", str(DEFAULT_LOCAL_FIRESTORE_CREDENTIALS))
        )
        if not credentials_path.is_file():
            logger.warning("Local Firestore credentials file not found: %s", credentials_path)
            return None

        credentials = service_account.Credentials.from_service_account_file(str(credentials_path))
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or credentials.project_id
        return firestore.Client(
            project=project_id,
            credentials=credentials,
            database=FIRESTORE_DATABASE_ID,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Firestore client initialization failed: %s", exc)
        return None


def update_last_access() -> bool:
    """Record dashboard access time in Firestore; return False on non-fatal failure."""
    client = _get_firestore_client()
    if client is None:
        return False

    try:
        client.collection("dashboard_state").document("sql_activity").set(
            {"last_access": datetime.now(timezone.utc)},
            merge=True,
        )
        return True
    except GoogleCloudError as exc:
        logger.warning("Failed to update Firestore dashboard_state/sql_activity: %s", exc)
        return False
    except Exception as exc:  # noqa: BLE001
        logger.warning("Unexpected Firestore update error: %s", exc)
        return False


def trigger_sql_wake_up() -> bool:
    """Trigger Cloud DB wake-up endpoint when configured."""

    wake_sql_url = setting.WAKE_SQL_URL
    if not wake_sql_url:
        logger.warning("WAKE_SQL_URL is not configured; cannot trigger DB wake-up.")
        return False

    project_id = setting.WAKE_SQL_PROJECT_ID
    instance_id = setting.WAKE_SQL_INSTANCE_ID
    if not project_id or not instance_id:
        logger.warning(
            "WAKE_SQL_PROJECT_ID or WAKE_SQL_INSTANCE_ID missing; cannot trigger DB wake-up."
        )
        return False

    ca_bundle_path = setting.WAKE_SQL_CA_BUNDLE_PATH or None
    client = WakeSqlFunctionClient(
        function_url=wake_sql_url,
        timeout_seconds=max(int(setting.WAKE_SQL_TIMEOUT_SECONDS), 1),
        poll_seconds=max(int(setting.WAKE_SQL_POLL_SECONDS), 1),
        max_wait_seconds=max(int(setting.WAKE_STATUS_MAX_WAIT_SECONDS), 1),
        verify_ssl=bool(setting.WAKE_SQL_VERIFY_SSL),
        ca_bundle_path=ca_bundle_path,
    )

    status_code, payload = client.call(project_id=project_id, instance_id=instance_id)
    if 200 <= status_code < 300:
        return True

    logger.warning(
        "Wake SQL request failed (status=%s) for URL '%s': %s",
        status_code,
        wake_sql_url,
        payload,
    )
    return False
