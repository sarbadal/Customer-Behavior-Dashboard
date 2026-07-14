function initDashboardCharts() {
    const dataElement = document.getElementById("dashboard-data");
    if (
        !dataElement ||
        typeof Chart === "undefined" ||
        !window.DashboardChartShared ||
        !window.DashboardChartBuilders
    ) {
        return;
    }

    const ctx = window.DashboardChartShared.createChartContext(dataElement);
    const builders = window.DashboardChartBuilders;

    builders.createBrowsingChart?.(ctx);
    builders.createDeviceChart?.(ctx);
    builders.createMonthlyRevenueChart?.(ctx);
    builders.createCityChart?.(ctx);
    builders.createTrafficSourceChart?.(ctx);
}

window.DashboardCharts = {
    initDashboardCharts
};
