import csv
import io
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


def _read_local_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


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

    if data_source == "local":
        local_data_dir = Path(setting.LOCAL_DATA_DIR)
        return _read_local_csv_rows(local_data_dir / path.name)

    if data_source != "gcp_bucket":
        raise RuntimeError("Invalid DATA_SOURCE in setting.py. Use 'local' or 'gcp_bucket'.")

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
