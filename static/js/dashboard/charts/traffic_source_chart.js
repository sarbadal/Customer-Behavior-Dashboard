function createTrafficSourceChart(ctx) {
    const canvas = document.getElementById("trafficSourceChart");
    if (!canvas) {
        return;
    }

    new Chart(canvas, {
        type: "bar",
        data: {
            labels: ctx.trafficLabels,
            datasets: [{
                label: "Events",
                data: ctx.trafficValues,
                backgroundColor: ["#1d4ed8", "#0f766e", "#f59e0b", "#ef4444", "#f97316", "#0891b2"],
                borderRadius: 8,
                maxBarThickness: 44
            }]
        },
        options: {
            indexAxis: "y",
            plugins: { legend: { display: false } },
            scales: {
                x: { beginAtZero: true, grid: ctx.commonGrid, ticks: ctx.commonTicks },
                y: { grid: { display: false }, ticks: ctx.commonTicks }
            }
        }
    });
}

window.DashboardChartBuilders = {
    ...(window.DashboardChartBuilders || {}),
    createTrafficSourceChart
};
