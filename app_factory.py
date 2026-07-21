import os
import logging
import secrets
from hmac import compare_digest
from urllib.parse import urlencode

from flask import Flask
from flask import redirect, render_template, request, session
from flask import url_for

import setting
from routes import register_dashboard_routes, register_health_routes, register_sql_wake_routes


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
    app_access_password = setting.APP_ACCESS_PASSWORD

    if setting.FLASK_SECRET_KEY:
        app.secret_key = setting.FLASK_SECRET_KEY
    else:
        logger.warning("FLASK_SECRET_KEY is not set; using ephemeral key for current process.")
        app.secret_key = secrets.token_hex(32)

    @app.route("/app-login", methods=["GET", "POST"])
    def app_login() -> str:
        if not app_access_password:
            return redirect(url_for("dashboard"))

        error = ""
        next_url = request.args.get("next", "").strip()

        if request.method == "POST":
            submitted_password = request.form.get("password", "")
            next_url = request.form.get("next", "").strip()
            if compare_digest(submitted_password, app_access_password):
                session["app_unlocked"] = True
                if next_url.startswith("/") and not next_url.startswith("//"):
                    return redirect(next_url)
                return redirect(url_for("dashboard"))
            error = "Invalid password. Please try again."

        return render_template("app_login.html", page_title="App Login", error_message=error, next_url=next_url)

    @app.post("/app-logout")
    def app_logout() -> str:
        session.pop("app_unlocked", None)
        return redirect(url_for("app_login"))

    @app.before_request
    def enforce_app_password():
        if not app_access_password:
            return None

        endpoint = request.endpoint or ""
        allowed_endpoints = {
            "app_login",
            "health",
            "health_data",
            "static",
        }
        if endpoint in allowed_endpoints:
            return None

        if session.get("app_unlocked"):
            return None

        next_path = request.full_path if request.query_string else request.path
        query = urlencode({"next": next_path})
        return redirect(f"{url_for('app_login')}?{query}")

    @app.template_global("asset_url")
    def asset_url(filename: str) -> str:
        """Resolve static asset URL from GCS/CDN in prod, else Flask static endpoint."""

        if static_asset_base_url:
            return f"{static_asset_base_url}/{filename.lstrip('/')}"
        return url_for("static", filename=filename)

    @app.template_global("app_password_enabled")
    def app_password_enabled() -> bool:
        """Expose whether app-level password mode is enabled."""

        return bool(app_access_password)

    register_dashboard_routes(app)
    register_health_routes(app)
    register_sql_wake_routes(app)
    return app