import os

from flask import Flask
from flask import url_for

from routes import register_dashboard_routes


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

    @app.template_global("asset_url")
    def asset_url(filename: str) -> str:
        """Resolve static asset URL from GCS/CDN in prod, else Flask static endpoint."""

        if static_asset_base_url:
            return f"{static_asset_base_url}/{filename.lstrip('/')}"
        return url_for("static", filename=filename)

    register_dashboard_routes(app)
    return app