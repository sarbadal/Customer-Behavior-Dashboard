from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import setting

try:
    from google.cloud import storage
except ImportError:  # pragma: no cover - dependency is optional outside gcp source mode
    storage = None

try:
    from google.oauth2 import service_account
except ImportError:  # pragma: no cover - only required when JSON key mode is enabled
    service_account = None

try:
    import yaml
except ImportError:  # pragma: no cover - optional fallback when dependency is unavailable
    yaml = None


_ALLOWED_CHART_TYPES = {
    "bar",
    "line",
    "doughnut",
    "pie",
    "polarArea",
    "radar",
}
_CHART_ORDER = ["browsing", "device", "revenue_trend", "city", "traffic"]
_CHART_DEFAULTS: dict[str, dict[str, Any]] = {
    "browsing": {
        "enabled": True,
        "title": "Top Browsing Categories",
        "type": "bar",
        "canvas_id": "browsingChart",
        "wide": False,
    },
    "device": {
        "enabled": True,
        "title": "Device Distribution",
        "type": "doughnut",
        "canvas_id": "deviceChart",
        "wide": False,
    },
    "revenue_trend": {
        "enabled": True,
        "title": "Revenue Trend",
        "type": "line",
        "canvas_id": "monthlyRevenueChart",
        "wide": True,
    },
    "city": {
        "enabled": True,
        "title": "Top Cities by Activity",
        "type": "polarArea",
        "canvas_id": "cityChart",
        "wide": False,
    },
    "traffic": {
        "enabled": True,
        "title": "Traffic Source Mix",
        "type": "bar",
        "canvas_id": "trafficSourceChart",
        "wide": False,
    },
}
_FILTER_DEFAULTS = {
    "region": True,
    "date_range": True,
    "trend": True,
}


def _create_gcs_client(project_id: str | None, use_json_key: bool, credentials_file: Path) -> "storage.Client":
    if storage is None:
        raise RuntimeError(
            "google-cloud-storage is required for gcp_bucket dashboard config mode. Install dependencies in runtime."
        )

    # Enforce global GCP auth mode: only use JSON key when GCP_USE_JSON_KEY is enabled.
    effective_use_json_key = bool(use_json_key and setting.GCP_USE_JSON_KEY)

    if not effective_use_json_key:
        return storage.Client(project=project_id or None)

    if service_account is None:
        raise RuntimeError("google-auth is required for JSON key mode.")

    if not credentials_file.exists():
        raise RuntimeError(f"GCP credentials file not found: {credentials_file}")

    credentials = service_account.Credentials.from_service_account_file(str(credentials_file))
    return storage.Client(project=project_id or None, credentials=credentials)


def _resolve_dashboard_config_bucket() -> str:
    if setting.DASHBOARD_CONFIG_GCS_BUCKET:
        return setting.DASHBOARD_CONFIG_GCS_BUCKET

    static_bucket = os.getenv("GCS_STATIC_BUCKET", "").strip()
    if static_bucket:
        return static_bucket

    return str(setting.GCP_BUCKET_NAME).strip()


def _load_local_yaml_text(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _load_gcs_yaml_text() -> str | None:
    bucket = _resolve_dashboard_config_bucket()
    object_name = str(setting.DASHBOARD_CONFIG_GCS_OBJECT).strip("/")
    if not bucket or not object_name:
        return None

    project_id = str(setting.DASHBOARD_CONFIG_GCS_PROJECT_ID).strip() or None
    use_json_key = bool(setting.DASHBOARD_CONFIG_GCS_USE_JSON_KEY)
    credentials_file = Path(setting.DASHBOARD_CONFIG_GCS_CREDENTIALS_FILE)

    try:
        gcs_client = _create_gcs_client(
            project_id=project_id,
            use_json_key=use_json_key,
            credentials_file=credentials_file,
        )
        gcs_bucket = gcs_client.bucket(bucket)
        blob = gcs_bucket.blob(object_name)
        if not blob.exists():
            return None
        return blob.download_as_text(encoding="utf-8")
    except Exception:
        return None


def _load_raw_config() -> dict[str, Any]:
    if yaml is None:
        return {}

    source = str(setting.DASHBOARD_CONFIG_SOURCE).strip().lower()
    yaml_text: str | None

    if source == "gcp_bucket":
        # Prefer GCS when requested, but gracefully fall back to local for resilience.
        yaml_text = _load_gcs_yaml_text() or _load_local_yaml_text(Path(setting.DASHBOARD_CONFIG_LOCAL_FILE))
    else:
        yaml_text = _load_local_yaml_text(Path(setting.DASHBOARD_CONFIG_LOCAL_FILE))

    if not yaml_text:
        return {}

    try:
        content = yaml.safe_load(yaml_text)
    except Exception:
        return {}

    return content if isinstance(content, dict) else {}


def _parse_filters(raw_config: dict[str, Any]) -> dict[str, bool]:
    raw_filters = raw_config.get("filters", {})
    if not isinstance(raw_filters, dict):
        raw_filters = {}

    return {
        "region": bool(raw_filters.get("region", _FILTER_DEFAULTS["region"])),
        "date_range": bool(raw_filters.get("date_range", _FILTER_DEFAULTS["date_range"])),
        "trend": bool(raw_filters.get("trend", _FILTER_DEFAULTS["trend"])),
    }


def _parse_charts(raw_config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    raw_charts = raw_config.get("charts", {})
    if not isinstance(raw_charts, dict):
        raw_charts = {}

    charts_for_template: list[dict[str, Any]] = []
    chart_config_for_js: dict[str, dict[str, Any]] = {}

    for chart_key in _CHART_ORDER:
        chart = _CHART_DEFAULTS[chart_key].copy()
        override = raw_charts.get(chart_key, {})
        if isinstance(override, dict):
            if "enabled" in override:
                chart["enabled"] = bool(override["enabled"])

            title = override.get("title")
            if isinstance(title, str) and title.strip():
                chart["title"] = title.strip()

            chart_type = override.get("type")
            if isinstance(chart_type, str) and chart_type in _ALLOWED_CHART_TYPES:
                chart["type"] = chart_type

        chart_config_for_js[chart_key] = {
            "enabled": bool(chart["enabled"]),
            "type": chart["type"],
        }

        if chart["enabled"]:
            charts_for_template.append(
                {
                    "key": chart_key,
                    "title": chart["title"],
                    "canvas_id": chart["canvas_id"],
                    "wide": chart["wide"],
                }
            )

    return charts_for_template, chart_config_for_js


@lru_cache(maxsize=1)
def get_dashboard_ui_config() -> dict[str, Any]:
    """Return dashboard UI configuration from YAML with safe defaults."""

    raw_config = _load_raw_config()
    filters = _parse_filters(raw_config)
    charts, chart_js_config = _parse_charts(raw_config)

    return {
        "filters": filters,
        "charts": charts,
        "chart_config_json": json.dumps(chart_js_config),
    }
