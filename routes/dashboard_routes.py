from urllib.parse import urlencode
import logging

from flask import Flask, redirect, render_template, request, session, url_for

import setting

from services.dashboard_service import DashboardContextInput, build_dashboard_context
from utils.dashboard_config import get_dashboard_ui_config
from utils.csv_loader import check_runtime_db_ready

from services.sql_wake_up import update_last_access


logger = logging.getLogger(__name__)


def _should_redirect_to_loading() -> bool:
    """Return True when MySQL is not ready and loading flow should be shown."""

    if setting.DATA_SOURCE != "mysql":
        return False

    if session.get("mysql_ready"):
        return False

    # Fallback to a direct readiness probe in case session state was not persisted.
    is_healthy, details = check_runtime_db_ready()
    is_cloud_db_ready = bool(is_healthy and details.get("data_source") == "mysql")
    if is_cloud_db_ready:
        session["mysql_ready"] = True
        return False

    return True


def _is_mysql_connection_error(exc: Exception) -> bool:
    """Best-effort detection for transient MySQL connectivity issues."""

    current: Exception | None = exc
    while current is not None:
        name = current.__class__.__name__
        message = str(current).lower()

        if name in {"OperationalError", "InterfaceError"}:
            if any(
                token in message
                for token in [
                    "can't connect",
                    "timed out",
                    "connection",
                    "lost connection",
                    "refused",
                ]
            ):
                return True

        next_exc = current.__cause__ or current.__context__
        current = next_exc if isinstance(next_exc, Exception) else None

    return False


def dashboard() -> str:
    """Render the main dashboard page with optional filters."""

    if _should_redirect_to_loading():
        args_multi = request.args.to_dict(flat=False)
        query = urlencode(args_multi, doseq=True)
        next_url = f"{request.path}?{query}" if query else request.path
        return redirect(url_for("loading_dashboard", next=next_url))

    update_last_access()

    selected_regions = [region.strip() for region in request.args.getlist("region") if region.strip()]
    trend_granularity = request.args.get("trend", "monthly").strip().lower()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    try:
        context = build_dashboard_context(
            DashboardContextInput(
                selected_regions=selected_regions,
                trend_granularity=trend_granularity,
                start_date=start_date,
                end_date=end_date,
            )
        )
    except Exception as exc:  # noqa: BLE001
        # If MySQL goes unavailable between READY checks, return to loading flow instead of 500.
        if setting.DATA_SOURCE == "mysql" and _is_mysql_connection_error(exc):
            logger.warning("Dashboard MySQL read failed; redirecting to loading flow: %s", exc)
            session.pop("mysql_ready", None)
            args_multi = request.args.to_dict(flat=False)
            query = urlencode(args_multi, doseq=True)
            next_url = f"{request.path}?{query}" if query else request.path
            return redirect(url_for("loading_dashboard", next=next_url))
        logger.exception("Dashboard rendering failed with non-connection error.")
        raise
    context["session_warning_delay_ms"] = max(setting.SESSION_WARNING_DELAY_MINUTES, 0) * 60_000
    context["ui_config"] = get_dashboard_ui_config()
    return render_template("dashboard.html", **context)


def loading_dashboard() -> str:
    next_url = request.args.get("next", "").strip()
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = url_for("dashboard")
    return render_template("loading.html", dashboard_url=next_url)


def about() -> str:
    kpi_definitions = [
        {
            "name": "Total Users",
            "definition": "Count of unique user_id values across browsing, purchase, and location datasets.",
        },
        {
            "name": "Total Sessions",
            "definition": "Count of unique session_id values in browsing_history table.",
        },
        {
            "name": "Total Orders",
            "definition": "Count of unique order_id values in purchase_patterns table.",
        },
        {
            "name": "Revenue",
            "definition": "Sum of order_value from purchase_patterns table after numeric parsing.",
        },
        {
            "name": "Avg Time / Page",
            "definition": "Average of time_spent_seconds from browsing_history table.",
        },
    ]

    data_dictionary = [
        {
            "dataset": "browsing_history",
            "fields": [
                "user_id",
                "session_id",
                "timestamp",
                "category",
                "device",
                "time_spent_seconds",
            ],
        },
        {
            "dataset": "purchase_patterns",
            "fields": [
                "user_id",
                "order_id",
                "order_timestamp",
                "order_value",
            ],
        },
        {
            "dataset": "location_data",
            "fields": [
                "user_id",
                "event_timestamp",
                "city",
                "region",
                "traffic_source",
            ],
        },
    ]

    return render_template(
        "about.html",
        page_title="About | Customer Behavioral Insights",
        kpi_definitions=kpi_definitions,
        data_dictionary=data_dictionary,
    )


def register_dashboard_routes(app: Flask) -> None:
    """Attach dashboard-related routes to the Flask app."""

    app.add_url_rule("/", endpoint="dashboard", view_func=dashboard)
    app.add_url_rule("/loading", endpoint="loading_dashboard", view_func=loading_dashboard)
    app.add_url_rule("/about", endpoint="about", view_func=about)
