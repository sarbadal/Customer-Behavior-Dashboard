from .dashboard_routes import register_dashboard_routes
from .health_routes import register_health_routes
from .sql_wake_up import register_sql_wake_up_routes


__all__ = ["register_dashboard_routes", "register_health_routes", "register_sql_wake_up_routes"]
