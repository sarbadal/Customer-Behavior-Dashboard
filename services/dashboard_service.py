from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

from core.config import DATA_DIR
from utils.csv_loader import read_csv_rows
from utils.parsers import safe_float, safe_int


@dataclass(frozen=True)
class DashboardRows:
    """Container for dashboard input datasets loaded from CSV files."""

    browsing_rows: list[dict[str, str]]
    purchase_rows: list[dict[str, str]]
    location_rows: list[dict[str, str]]


@dataclass(frozen=True)
class DashboardMetrics:
    """Typed KPI values displayed in the dashboard metric cards."""

    total_users: int
    total_sessions: int
    total_orders: int
    total_revenue: float
    avg_time_spent: float


@dataclass(frozen=True)
class DashboardCharts:
    """Typed Chart.js payloads serialized as JSON strings for the template."""

    browsing_labels: str
    browsing_values: str
    device_labels: str
    device_values: str
    monthly_labels: str
    monthly_values: str
    monthly_orders_values: str
    monthly_avg_order_value: str
    city_labels: str
    city_values: str
    traffic_labels: str
    traffic_values: str


@dataclass(frozen=True)
class MonthlySeries:
    """Typed output for revenue trend series across a selected time grain."""

    labels: list[str]
    revenue_values: list[float]
    orders_values: list[int]
    avg_order_value: list[float]


@dataclass(frozen=True)
class DashboardFilters:
    """Filter metadata used to render and preserve UI filter state."""

    regions: list[str]
    selected_regions: list[str]
    trend_granularity: str
    trend_granularity_options: list[str]
    start_date: str
    end_date: str
    min_date: str
    max_date: str


@dataclass(frozen=True)
class RegionFilterInput:
    """Typed input payload for building region and trend filter metadata."""

    location_rows: list[dict[str, str]]
    selected_regions: list[str] | None
    trend_granularity: str
    start_date: str
    end_date: str
    min_date: str
    max_date: str


@dataclass(frozen=True)
class DashboardContextInput:
    """Typed input payload for building dashboard context from request filters."""

    selected_regions: list[str] | None = None
    trend_granularity: str = "monthly"
    start_date: str = ""
    end_date: str = ""


def _coerce_datetime(value: object) -> datetime | None:
    """Best-effort conversion of common timestamp value types to datetime."""

    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError:
            return None
    if not isinstance(value, str):
        return None

    text = value.strip()
    if not text:
        return None

    # Support UTC suffix used by some exports while still accepting ISO strings.
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"

    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _load_dashboard_rows() -> DashboardRows:
    """Load raw browsing, purchase, and location rows from the data folder."""

    browsing_rows = read_csv_rows(DATA_DIR / "browsing_history.csv")
    purchase_rows = read_csv_rows(DATA_DIR / "purchase_patterns.csv")
    location_rows = read_csv_rows(DATA_DIR / "location_data.csv")
    return DashboardRows(
        browsing_rows=browsing_rows,
        purchase_rows=purchase_rows,
        location_rows=location_rows,
    )


def _build_region_filters(params: RegionFilterInput) -> DashboardFilters:
    """Build available/selected region values for the filter dropdown."""

    regions = sorted(
        {row.get("region", "").strip() for row in params.location_rows if row.get("region", "").strip()}
    )
    normalized_selected = []
    if params.selected_regions:
        for region in params.selected_regions:
            trimmed = region.strip()
            if trimmed and trimmed in regions and trimmed not in normalized_selected:
                normalized_selected.append(trimmed)

    allowed_granularities = ["daily", "weekly", "monthly", "quarterly", "yearly"]
    normalized_granularity = (
        params.trend_granularity if params.trend_granularity in allowed_granularities else "monthly"
    )

    return DashboardFilters(
        regions=regions,
        selected_regions=normalized_selected,
        trend_granularity=normalized_granularity,
        trend_granularity_options=allowed_granularities,
        start_date=params.start_date,
        end_date=params.end_date,
        min_date=params.min_date,
        max_date=params.max_date,
    )


def _extract_date_bounds(rows: DashboardRows) -> tuple[str, str]:
    """Compute dataset-wide min and max date (yyyy-mm-dd) across all timestamp fields."""

    timestamps: list[datetime] = []
    time_fields = (
        (rows.browsing_rows, "timestamp"),
        (rows.purchase_rows, "order_timestamp"),
        (rows.location_rows, "event_timestamp"),
    )

    for dataset, field in time_fields:
        for row in dataset:
            row_dt = _coerce_datetime(row.get(field))
            if row_dt is None:
                continue
            timestamps.append(row_dt)

    if not timestamps:
        return "", ""

    return min(timestamps).strftime("%Y-%m-%d"), max(timestamps).strftime("%Y-%m-%d")


def _normalize_date_input(date_text: str) -> str:
    """Return yyyy-mm-dd only when the input date is valid."""

    if not date_text:
        return ""
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return ""


def _apply_date_range_filter(rows: DashboardRows, start_date: str, end_date: str) -> DashboardRows:
    """Filter datasets using inclusive date bounds against each row timestamp field."""

    if not start_date and not end_date:
        return rows

    start_dt = datetime.min
    end_dt = datetime.max
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) - timedelta(microseconds=1)

    def within_bounds(row: dict[str, str], ts_key: str) -> bool:
        row_dt = _coerce_datetime(row.get(ts_key))
        if row_dt is None:
            return False
        return start_dt <= row_dt <= end_dt

    return DashboardRows(
        browsing_rows=[row for row in rows.browsing_rows if within_bounds(row, "timestamp")],
        purchase_rows=[row for row in rows.purchase_rows if within_bounds(row, "order_timestamp")],
        location_rows=[row for row in rows.location_rows if within_bounds(row, "event_timestamp")],
    )


def _apply_region_filter(rows: DashboardRows, selected_regions: list[str]) -> DashboardRows:
    """Filter all datasets to users present in the selected regions."""

    if not selected_regions:
        return rows

    selected_set = set(selected_regions)
    location_rows = [r for r in rows.location_rows if r.get("region", "").strip() in selected_set]
    allowed_users = {row.get("user_id", "") for row in location_rows if row.get("user_id")}

    browsing_rows = [r for r in rows.browsing_rows if r.get("user_id", "") in allowed_users]
    purchase_rows = [r for r in rows.purchase_rows if r.get("user_id", "") in allowed_users]

    return DashboardRows(
        browsing_rows=browsing_rows,
        purchase_rows=purchase_rows,
        location_rows=location_rows,
    )


def _build_metrics(rows: DashboardRows) -> DashboardMetrics:
    """Compute top-level KPI metrics used by the dashboard cards."""

    total_users = len(
        {
            row.get("user_id", "")
            for row in rows.browsing_rows + rows.purchase_rows + rows.location_rows
            if row.get("user_id")
        }
    )

    total_sessions = len(
        {row.get("session_id", "") for row in rows.browsing_rows if row.get("session_id")}
    )
    total_orders = len({row.get("order_id", "") for row in rows.purchase_rows if row.get("order_id")})
    total_revenue = sum(safe_float(row.get("order_value")) for row in rows.purchase_rows)

    avg_time_spent = 0.0
    if rows.browsing_rows:
        avg_time_spent = sum(safe_int(r.get("time_spent_seconds")) for r in rows.browsing_rows) / len(
            rows.browsing_rows
        )

    return DashboardMetrics(
        total_users=total_users,
        total_sessions=total_sessions,
        total_orders=total_orders,
        total_revenue=round(total_revenue, 2),
        avg_time_spent=round(avg_time_spent, 1),
    )


def _build_trend_series(purchase_rows: list[dict[str, str]], granularity: str) -> MonthlySeries:
    """Aggregate revenue, order count, and average order value for a selected time grain."""

    # Define bucket formatters for different time granularities (daily, weekly, monthly, quarterly, yearly)

    def _daily_bucket(dt: datetime) -> str:
        """Return yyyy-mm-dd for daily granularity."""
        return dt.strftime("%Y-%m-%d")

    def _weekly_bucket(dt: datetime) -> str:
        """Return yyyy-mm-dd of the Monday for weekly granularity."""
        monday = dt - timedelta(days=dt.weekday())
        return monday.strftime("%Y-%m-%d")

    def _monthly_bucket(dt: datetime) -> str:
        """Return yyyy-mm for monthly granularity."""
        return dt.strftime("%Y-%m")

    def _quarterly_bucket(dt: datetime) -> str:
        """Return yyyy-Qn for quarterly granularity."""
        quarter = ((dt.month - 1) // 3) + 1
        return f"{dt.year}-Q{quarter}"

    def _yearly_bucket(dt: datetime) -> str:
        """Return yyyy for yearly granularity."""
        return str(dt.year)

    bucket_formatters = {
        "daily": _daily_bucket,
        "weekly": _weekly_bucket,
        "monthly": _monthly_bucket,
        "quarterly": _quarterly_bucket,
        "yearly": _yearly_bucket,
    }

    # Define a function to get the bucket key based on the selected granularity
    def bucket_key(dt: datetime) -> str:
        """Return the appropriate bucket key for the given datetime based on the selected granularity."""
        formatter = bucket_formatters.get(granularity, bucket_formatters["monthly"])
        return formatter(dt)

    monthly_revenue_map: dict[str, float] = defaultdict(float)
    monthly_orders_map: dict[str, int] = defaultdict(int)
    for row in purchase_rows:
        row_dt = _coerce_datetime(row.get("order_timestamp"))
        if row_dt is None:
            continue
        time_key = bucket_key(row_dt)
        monthly_revenue_map[time_key] += safe_float(row.get("order_value"))
        monthly_orders_map[time_key] += 1

    months = sorted(monthly_revenue_map.keys())
    monthly_revenue = [round(monthly_revenue_map[month], 2) for month in months]
    monthly_orders = [monthly_orders_map[month] for month in months]
    monthly_avg_order_value = [
        round(monthly_revenue_map[month] / monthly_orders_map[month], 2) if monthly_orders_map[month] > 0 else 0.0
        for month in months
    ]

    return MonthlySeries(
        labels=months,
        revenue_values=monthly_revenue,
        orders_values=monthly_orders,
        avg_order_value=monthly_avg_order_value,
    )


def build_dashboard_context(params: DashboardContextInput) -> dict[str, dict[str, object]]:
    """Assemble template context containing metrics and chart payloads."""

    normalized_start_date = _normalize_date_input(params.start_date)
    normalized_end_date = _normalize_date_input(params.end_date)

    raw_rows = _load_dashboard_rows()
    min_date, max_date = _extract_date_bounds(raw_rows)
    date_filtered_rows = _apply_date_range_filter(raw_rows, normalized_start_date, normalized_end_date)
    filters = _build_region_filters(
        RegionFilterInput(
            location_rows=date_filtered_rows.location_rows,
            selected_regions=params.selected_regions,
            trend_granularity=params.trend_granularity,
            start_date=normalized_start_date,
            end_date=normalized_end_date,
            min_date=min_date,
            max_date=max_date,
        )
    )
    rows = _apply_region_filter(date_filtered_rows, filters.selected_regions)

    metrics = _build_metrics(rows)
    charts = _build_charts(rows, filters.trend_granularity)

    return {
        "metrics": asdict(metrics),
        "charts": asdict(charts),
        "filters": asdict(filters),
    }


def _build_charts(rows: DashboardRows, trend_granularity: str) -> DashboardCharts:
    """Build chart payloads using the requested time granularity for trend lines."""

    browsing_category_counts = Counter(row.get("category", "Unknown") for row in rows.browsing_rows)
    top_browsing = browsing_category_counts.most_common(7)

    device_counts = Counter(row.get("device", "Unknown") for row in rows.browsing_rows)
    device_distribution = device_counts.most_common()

    trend_series = _build_trend_series(
        rows.purchase_rows,
        trend_granularity,
    )

    city_counts = Counter(row.get("city", "Unknown") for row in rows.location_rows)
    top_cities = city_counts.most_common(8)

    traffic_source_counts = Counter(row.get("traffic_source", "Unknown") for row in rows.location_rows)
    top_traffic_sources = traffic_source_counts.most_common(6)

    return DashboardCharts(
        browsing_labels=json.dumps([x[0] for x in top_browsing]),
        browsing_values=json.dumps([x[1] for x in top_browsing]),
        device_labels=json.dumps([x[0] for x in device_distribution]),
        device_values=json.dumps([x[1] for x in device_distribution]),
        monthly_labels=json.dumps(trend_series.labels),
        monthly_values=json.dumps(trend_series.revenue_values),
        monthly_orders_values=json.dumps(trend_series.orders_values),
        monthly_avg_order_value=json.dumps(trend_series.avg_order_value),
        city_labels=json.dumps([x[0] for x in top_cities]),
        city_values=json.dumps([x[1] for x in top_cities]),
        traffic_labels=json.dumps([x[0] for x in top_traffic_sources]),
        traffic_values=json.dumps([x[1] for x in top_traffic_sources]),
    )
