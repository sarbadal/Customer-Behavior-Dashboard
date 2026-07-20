from flask import Flask, jsonify

from services.sql_wake_up import update_last_access


def register_sql_wake_routes(app: Flask) -> None:
    """Attach SQL wake-up and activity tracking routes."""

    @app.get("/heartbeat")
    def heartbeat() -> tuple[object, int]:
        print("heartbeat called")
        # collection: dashboard_state, document: sql_activity, field: last_access
        access_updated = update_last_access()
        return jsonify({"status": "alive", "activity_updated": access_updated}), 200

    @app.get("/wake-status")
    def wake_status() -> tuple[object, int]:
        # TODO: Later replace with Cloud SQL status check
        return jsonify({"state": "READY"}), 200
     

