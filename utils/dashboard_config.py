from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import setting

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


_ALLOWED_CHART_TYPES = {
    "bar",
    "line",
    "doughnut",
    "pie",
    "polarArea",
    "radar",
}
_CHART_ORDER = ["browsing", "device", "revenue_trend", "city", "traffic"]
_CHART_DEFAULTS: dict[str, dict[str, Any]] = {
    "browsing": {
        "enabled": True,
        "title": "Top Browsing Categories",
        "type": "bar",
        "canvas_id": "browsingChart",
        "wide": False,
    },
    "device": {
        "enabled": True,
        "title": "Device Distribution",
        "type": "doughnut",
        "canvas_id": "deviceChart",
        "wide": False,
    },
    "revenue_trend": {
        "enabled": True,
        "title": "Revenue Trend",
        "type": "line",
        "canvas_id": "monthlyRevenueChart",
        "wide": True,
    },
    "city": {
        "enabled": True,
        "title": "Top Cities by Activity",
        "type": "polarArea",
        "canvas_id": "cityChart",
        "wide": False,
    },
    "traffic": {
        "enabled": True,
        "title": "Traffic Source Mix",
        "type": "bar",
        "canvas_id": "trafficSourceChart",
        "wide": False,
    },
}
_FILTER_DEFAULTS = {
    "region": True,
    "date_range": True,
    "trend": True,
}


def _load_raw_config() -> dict[str, Any]:
    if yaml is None:
        return {}

    path = Path(setting.DASHBOARD_CONFIG_LOCAL_FILE)
    if not path.exists():
        return {}

    try:
        yaml_text = path.read_text(encoding="utf-8")
        content = yaml.safe_load(yaml_text)
    except Exception:
        return {}

    return content if isinstance(content, dict) else {}


def _parse_filters(raw_config: dict[str, Any]) -> dict[str, bool]:
    raw_filters = raw_config.get("filters", {})
    if not isinstance(raw_filters, dict):
        raw_filters = {}

    return {
        "region": bool(raw_filters.get("region", _FILTER_DEFAULTS["region"])),
        "date_range": bool(raw_filters.get("date_range", _FILTER_DEFAULTS["date_range"])),
        "trend": bool(raw_filters.get("trend", _FILTER_DEFAULTS["trend"])),
    }


def _parse_charts(raw_config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    raw_charts = raw_config.get("charts", {})
    if not isinstance(raw_charts, dict):
        raw_charts = {}

    charts_for_template: list[dict[str, Any]] = []
    chart_config_for_js: dict[str, dict[str, Any]] = {}

    for chart_key in _CHART_ORDER:
        chart = _CHART_DEFAULTS[chart_key].copy()
        override = raw_charts.get(chart_key, {})
        if isinstance(override, dict):
            if "enabled" in override:
                chart["enabled"] = bool(override["enabled"])

            title = override.get("title")
            if isinstance(title, str) and title.strip():
                chart["title"] = title.strip()

            chart_type = override.get("type")
            if isinstance(chart_type, str) and chart_type in _ALLOWED_CHART_TYPES:
                chart["type"] = chart_type

        chart_config_for_js[chart_key] = {
            "enabled": bool(chart["enabled"]),
            "type": chart["type"],
        }

        if chart["enabled"]:
            charts_for_template.append(
                {
                    "key": chart_key,
                    "title": chart["title"],
                    "canvas_id": chart["canvas_id"],
                    "wide": chart["wide"],
                }
            )

    return charts_for_template, chart_config_for_js


@lru_cache(maxsize=1)
def get_dashboard_ui_config() -> dict[str, Any]:
    raw_config = _load_raw_config()
    filters = _parse_filters(raw_config)
    charts, chart_js_config = _parse_charts(raw_config)

    return {
        "filters": filters,
        "charts": charts,
        "chart_config_json": json.dumps(chart_js_config),
    }
