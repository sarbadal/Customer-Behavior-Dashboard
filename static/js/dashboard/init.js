function bootstrapDashboard() {
    if (!window.DashboardCharts || !window.DashboardFilters) {
        return;
    }

    window.DashboardCharts.initDashboardCharts();
    window.DashboardFilters.initRegionFilterDropdown();
    window.DashboardFilters.initDateRangeFromQuery();
}

bootstrapDashboard();
