import os
import logging

from flask import Flask
from flask import url_for

import setting
from routes import register_dashboard_routes, register_health_routes, register_sql_wake_up_routes
from utils.db import bootstrap_mysql_from_local_sqlite_if_needed


logger = logging.getLogger(__name__)


def _resolve_static_base_url() -> str:
    """Resolve static asset base URL with GCS support and env overrides."""

    explicit_base = os.getenv("STATIC_ASSET_BASE_URL", "").rstrip("/")
    if explicit_base:
        return explicit_base

    # Build a public GCS URL when bucket is provided.
    gcs_bucket = os.getenv("GCS_STATIC_BUCKET", "").strip()
    gcs_prefix = os.getenv("GCS_STATIC_PREFIX", "").strip("/")

    if not gcs_bucket:
        return ""

    base = f"https://storage.googleapis.com/{gcs_bucket}"
    return f"{base}/{gcs_prefix}" if gcs_prefix else base


def create_app() -> Flask:
    """Create and configure the Flask application instance."""

    app = Flask(__name__)
    static_asset_base_url = _resolve_static_base_url()

    if setting.DB_AUTO_BOOTSTRAP_FROM_SQLITE:
        try:
            bootstrap_result = bootstrap_mysql_from_local_sqlite_if_needed()
            if bootstrap_result.get("status") not in {"ok", "skipped"}:
                logger.warning("DB bootstrap returned unexpected status: %s", bootstrap_result)
        except Exception as exc:
            if setting.DB_BOOTSTRAP_FAIL_HARD:
                raise
            logger.warning("DB bootstrap skipped due to connection/setup error: %s", exc)

    @app.template_global("asset_url")
    def asset_url(filename: str) -> str:
        """Resolve static asset URL from GCS/CDN in prod, else Flask static endpoint."""

        if static_asset_base_url:
            return f"{static_asset_base_url}/{filename.lstrip('/')}"
        return url_for("static", filename=filename)

    register_dashboard_routes(app)
    register_health_routes(app)
    register_sql_wake_up_routes(app)

    return app