from flask import Flask, render_template, request

from services.dashboard_service import DashboardContextInput, build_dashboard_context
from utils.dashboard_config import get_dashboard_ui_config


def register_dashboard_routes(app: Flask) -> None:
    """Attach dashboard-related routes to the Flask app."""

    @app.route("/")
    def dashboard() -> str:
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
        context["ui_config"] = get_dashboard_ui_config()
        return render_template("dashboard.html", **context)

    @app.route("/about")
    def about() -> str:
        kpi_definitions = [
            {
                "name": "Total Users",
                "definition": "Count of unique user_id values across browsing, purchase, and location datasets.",
            },
            {
                "name": "Total Sessions",
                "definition": "Count of unique session_id values in browsing_history.csv.",
            },
            {
                "name": "Total Orders",
                "definition": "Count of unique order_id values in purchase_patterns.csv.",
            },
            {
                "name": "Revenue",
                "definition": "Sum of order_value from purchase_patterns.csv after numeric parsing.",
            },
            {
                "name": "Avg Time / Page",
                "definition": "Average of time_spent_seconds from browsing_history.csv.",
            },
        ]

        data_dictionary = [
            {
                "dataset": "browsing_history.csv",
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
                "dataset": "purchase_patterns.csv",
                "fields": [
                    "user_id",
                    "order_id",
                    "order_timestamp",
                    "order_value",
                ],
            },
            {
                "dataset": "location_data.csv",
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
