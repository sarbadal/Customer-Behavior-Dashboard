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

    let chartConfig = {};
    const rawConfig = dataElement.getAttribute("data-chart-config");
    if (rawConfig) {
        try {
            chartConfig = JSON.parse(rawConfig);
        } catch (error) {
            console.error("Failed to parse chart config:", error);
        }
    }

    const chartRegistry = [
        { key: "browsing", builder: builders.createBrowsingChart },
        { key: "device", builder: builders.createDeviceChart },
        { key: "revenue_trend", builder: builders.createMonthlyRevenueChart },
        { key: "city", builder: builders.createCityChart },
        { key: "traffic", builder: builders.createTrafficSourceChart }
    ];

    chartRegistry.forEach(({ key, builder }) => {
        if (!builder) {
            return;
        }

        const config = chartConfig[key] || {};
        if (config.enabled === false) {
            return;
        }

        try {
            builder(ctx, config);
        } catch (error) {
            console.error(`Failed to render chart: ${key}`, error);
        }
    });
}

window.DashboardCharts = {
    initDashboardCharts
};
