from flask import Flask, render_template, request

import setting

from services.dashboard_service import DashboardContextInput, build_dashboard_context
from utils.dashboard_config import get_dashboard_ui_config

from services.sql_wake_up import update_last_access


def dashboard() -> str:
    """Render the main dashboard page with optional filters."""
    update_last_access()

    selected_regions = [region.strip() for region in request.args.getlist("region") if region.strip()]
    trend_granularity = request.args.get("trend", "monthly").strip().lower()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    context = build_dashboard_context(
        DashboardContextInput(
            selected_regions=selected_regions,
            trend_granularity=trend_granularity,
            start_date=start_date,
            end_date=end_date,
        )
    )
    context["session_warning_delay_ms"] = max(setting.SESSION_WARNING_DELAY_MINUTES, 0) * 60_000
    context["ui_config"] = get_dashboard_ui_config()
    return render_template("dashboard.html", **context)


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
    app.add_url_rule("/about", endpoint="about", view_func=about)
