function createChartContext(dataElement) {
    const { parseJsonAttr } = window.DashboardUtils;

    Chart.defaults.font.family = '"Space Grotesk", sans-serif';
    Chart.defaults.font.size = 13;
    Chart.defaults.font.weight = "500";
    Chart.defaults.color = "#1f3440";
    Chart.defaults.borderColor = "rgba(28, 57, 71, 0.2)";
    Chart.defaults.elements.line.borderWidth = 2.5;
    Chart.defaults.elements.point.borderWidth = 1.2;
    Chart.defaults.elements.point.hoverRadius = 5;

    const isNarrow = window.matchMedia("(max-width: 1100px)").matches;

    return {
        browsingLabels: parseJsonAttr(dataElement, "data-browsing-labels"),
        browsingValues: parseJsonAttr(dataElement, "data-browsing-values"),
        deviceLabels: parseJsonAttr(dataElement, "data-device-labels"),
        deviceValues: parseJsonAttr(dataElement, "data-device-values"),
        monthlyLabels: parseJsonAttr(dataElement, "data-monthly-labels"),
        monthlyValues: parseJsonAttr(dataElement, "data-monthly-values"),
        monthlyOrdersValues: parseJsonAttr(dataElement, "data-monthly-orders-values"),
        monthlyAvgOrderValue: parseJsonAttr(dataElement, "data-monthly-avg-order-value"),
        cityLabels: parseJsonAttr(dataElement, "data-city-labels"),
        cityValues: parseJsonAttr(dataElement, "data-city-values"),
        trafficLabels: parseJsonAttr(dataElement, "data-traffic-labels"),
        trafficValues: parseJsonAttr(dataElement, "data-traffic-values"),
        commonGrid: {
            color: "rgba(28, 57, 71, 0.18)",
            lineWidth: 1,
            borderDash: [3, 3],
            tickLength: 6,
            drawTicks: true
        },
        commonTicks: {
            color: "#1f3440",
            font: {
                size: 12,
                weight: "600"
            },
            padding: 6
        },
        isNarrow,
        legendFontSize: isNarrow ? 14 : 16
    };
}

window.DashboardChartShared = {
    createChartContext
};
