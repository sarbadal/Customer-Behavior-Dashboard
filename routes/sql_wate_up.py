from flask import Flask, jsonify

from services.sql_wate_up import update_last_access


def register_health_routes(app: Flask) -> None:
    """Attach health-check routes for runtime and data source validation."""

    @app.get("/heartbeat")
    def heartbeat() -> tuple[object, int]:
        access_updated = update_last_access()
        return jsonify({"status": "alive", "activity_updated": access_updated}), 200

    @app.get("/wake-status")
    def wake_status() -> tuple[object, int]:
        # TODO: Later replace with Cloud SQL status check
        return jsonify({"state": "READY"}), 200
     

