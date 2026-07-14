function createMonthlyRevenueChart(ctx) {
    const canvas = document.getElementById("monthlyRevenueChart");
    if (!canvas) {
        return;
    }

    new Chart(canvas, {
        type: "line",
        data: {
            labels: ctx.monthlyLabels,
            datasets: [
                {
                    label: "Revenue",
                    data: ctx.monthlyValues,
                    fill: false,
                    borderColor: "#0f766e",
                    tension: 0.34,
                    pointRadius: 3,
                    pointBackgroundColor: "#0f766e",
                    yAxisID: "yRevenue"
                },
                {
                    label: "Orders",
                    data: ctx.monthlyOrdersValues,
                    fill: false,
                    borderColor: "#1d4ed8",
                    tension: 0.34,
                    pointRadius: 3,
                    pointBackgroundColor: "#1d4ed8",
                    yAxisID: "yOrders"
                },
                {
                    label: "Avg Order Value",
                    data: ctx.monthlyAvgOrderValue,
                    fill: false,
                    borderColor: "#f59e0b",
                    tension: 0.34,
                    borderDash: [6, 4],
                    pointRadius: 3,
                    pointBackgroundColor: "#f59e0b",
                    yAxisID: "yAvg"
                }
            ]
        },
        options: {
            plugins: {
                legend: {
                    position: "top"
                }
            },
            scales: {
                yRevenue: {
                    beginAtZero: true,
                    position: "left",
                    grid: ctx.commonGrid,
                    ticks: ctx.commonTicks,
                    title: {
                        display: true,
                        text: "Revenue"
                    }
                },
                yOrders: {
                    beginAtZero: true,
                    position: "right",
                    grid: {
                        display: false
                    },
                    ticks: ctx.commonTicks,
                    title: {
                        display: true,
                        text: "Orders"
                    }
                },
                yAvg: {
                    beginAtZero: true,
                    position: "right",
                    offset: true,
                    grid: {
                        display: false
                    },
                    ticks: ctx.commonTicks,
                    title: {
                        display: true,
                        text: "Avg Order Value"
                    }
                },
                x: { grid: { display: false }, ticks: ctx.commonTicks }
            }
        }
    });
}

window.DashboardChartBuilders = {
    ...(window.DashboardChartBuilders || {}),
    createMonthlyRevenueChart
};
