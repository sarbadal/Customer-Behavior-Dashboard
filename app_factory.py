import os

from flask import Flask
from flask import url_for

from routes import register_dashboard_routes


def create_app() -> Flask:
    """Create and configure the Flask application instance."""

    app = Flask(__name__)

    static_asset_base_url = os.getenv("STATIC_ASSET_BASE_URL", "").rstrip("/")

    @app.template_global("asset_url")
    def asset_url(filename: str) -> str:
        """Resolve static asset URL from bucket/CDN in prod, else Flask static endpoint."""

        if static_asset_base_url:
            return f"{static_asset_base_url}/{filename.lstrip('/')}"
        return url_for("static", filename=filename)

    register_dashboard_routes(app)
    return app
