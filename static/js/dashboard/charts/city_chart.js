function createCityChart(ctx) {
    const canvas = document.getElementById("cityChart");
    if (!canvas) {
        return;
    }

    new Chart(canvas, {
        type: "polarArea",
        data: {
            labels: ctx.cityLabels,
            datasets: [{
                data: ctx.cityValues,
                backgroundColor: [
                    "rgba(29, 78, 216, 0.75)",
                    "rgba(15, 118, 110, 0.75)",
                    "rgba(245, 158, 11, 0.75)",
                    "rgba(239, 68, 68, 0.75)",
                    "rgba(249, 115, 22, 0.75)",
                    "rgba(16, 185, 129, 0.75)",
                    "rgba(8, 145, 178, 0.75)",
                    "rgba(100, 116, 139, 0.75)"
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    right: ctx.isNarrow ? 0 : 8
                }
            },
            scales: { r: { grid: ctx.commonGrid } },
            plugins: {
                legend: {
                    position: ctx.isNarrow ? "bottom" : "right",
                    maxWidth: ctx.isNarrow ? undefined : 150,
                    labels: {
                        boxWidth: 12,
                        boxHeight: 12,
                        padding: 10,
                        font: {
                            size: 12
                        }
                    }
                }
            }
        }
    });
}

window.DashboardChartBuilders = {
    ...(window.DashboardChartBuilders || {}),
    createCityChart
};
