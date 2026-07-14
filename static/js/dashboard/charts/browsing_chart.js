function createBrowsingChart(ctx) {
    const canvas = document.getElementById("browsingChart");
    if (!canvas) {
        return;
    }

    new Chart(canvas, {
        type: "bar",
        data: {
            labels: ctx.browsingLabels,
            datasets: [{
                label: "Visits",
                data: ctx.browsingValues,
                backgroundColor: ["#0f766e", "#1d4ed8", "#f59e0b", "#ef4444", "#10b981", "#3b82f6", "#f97316"],
                borderRadius: 8,
                maxBarThickness: 38
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
    createBrowsingChart
};
