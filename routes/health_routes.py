from flask import Flask, jsonify

from utils.csv_loader import check_data_source_health


def register_health_routes(app: Flask) -> None:
    """Attach health-check routes for runtime and data source validation."""

    @app.get("/health")
    def health() -> tuple[object, int]:
        return jsonify({"status": "ok"}), 200

    @app.get("/health/data")
    def health_data() -> tuple[object, int]:
        is_healthy, details = check_data_source_health()
        payload = {
            "status": "ok" if is_healthy else "error",
            "checks": {
                "data_source": details,
            },
        }
        return jsonify(payload), 200 if is_healthy else 503
