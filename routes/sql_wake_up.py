from flask import Flask, jsonify, session
import time
import logging

import setting
from services.sql_wake_up import trigger_sql_wake_up, update_last_access
from utils.csv_loader import check_runtime_db_ready


logger = logging.getLogger(__name__)


def register_sql_wake_routes(app: Flask) -> None:
    """Attach SQL wake-up and activity tracking routes."""

    wake_timeout_seconds = max(int(setting.WAKE_STATUS_MAX_WAIT_SECONDS), 1)

    @app.get("/heartbeat")
    def heartbeat() -> tuple[object, int]:
        access_updated = update_last_access()
        return jsonify({"status": "alive", "activity_updated": access_updated}), 200

    @app.get("/wake-status")
    def wake_status() -> tuple[object, int]:
        def emit_status(state: str, details: dict[str, object] | None = None) -> None:
            message = f"[wake-status] state={state} source={'cloud_db' if setting.DATA_SOURCE == 'mysql' else 'local'}"
            if details and details.get("message"):
                message = f"{message} details={details.get('message')}"
            print(message)
            logger.info(message)

        if setting.DATA_SOURCE != "mysql":
            session["mysql_ready"] = True
            emit_status("READY")
            return jsonify({"state": "READY", "source": "local"}), 200

        now = time.time()
        is_healthy, details = check_runtime_db_ready()
        is_cloud_db_ready = bool(is_healthy and details.get("data_source") == "mysql")

        if is_cloud_db_ready:
            session["mysql_ready"] = True
            session.pop("mysql_wake_started_at", None)
            emit_status("READY", details)
            return jsonify({"state": "READY", "source": "cloud_db", "details": details}), 200

        session.pop("mysql_ready", None)
        wake_started_at = session.get("mysql_wake_started_at")

        if wake_started_at is None:
            wake_triggered = trigger_sql_wake_up()
            session["mysql_wake_started_at"] = now
            emit_status("STOPED", details)
            return (
                jsonify(
                    {
                        "state": "STOPED",
                        "source": "cloud_db",
                        "wake_triggered": wake_triggered,
                        "timeout_seconds": wake_timeout_seconds,
                        "details": details,
                    }
                ),
                200,
            )

        elapsed_seconds = max(int(now - float(wake_started_at)), 0)
        if elapsed_seconds >= wake_timeout_seconds:
            session.pop("mysql_wake_started_at", None)
            emit_status("TIMEOUT", details)
            return (
                jsonify(
                    {
                        "state": "TIMEOUT",
                        "source": "cloud_db",
                        "elapsed_seconds": elapsed_seconds,
                        "timeout_seconds": wake_timeout_seconds,
                        "details": details,
                    }
                ),
                200,
            )

        emit_status("WAKING", details)
        return (
            jsonify(
                {
                    "state": "WAKING",
                    "source": "cloud_db",
                    "elapsed_seconds": elapsed_seconds,
                    "timeout_seconds": wake_timeout_seconds,
                    "details": details,
                }
            ),
            200,
        )
     

