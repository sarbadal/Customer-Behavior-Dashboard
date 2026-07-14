function createBrowsingChart(ctx, config = {}) {
    const canvas = document.getElementById("browsingChart");
    if (!canvas) {
        return;
    }

    const chartType = config.type || "bar";
    const circularTypes = new Set(["doughnut", "pie", "polarArea", "radar"]);
    const isCircular = circularTypes.has(chartType);

    if (isCircular) {
        canvas.style.removeProperty("aspect-ratio");
        canvas.style.setProperty("height", ctx.isNarrow ? "220px" : "240px", "important");
    } else {
        canvas.style.removeProperty("aspect-ratio");
        canvas.style.removeProperty("height");
    }

    const options = isCircular
        ? {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: ctx.isNarrow ? "bottom" : "right",
                    labels: {
                        generateLabels(chart) {
                            const original = Chart.overrides.doughnut.plugins.legend.labels.generateLabels(chart);
                            const values = chart.data.datasets[0].data || [];
                            const total = values.reduce((sum, value) => sum + Number(value || 0), 0);

                            return original.map((item) => {
                                const value = Number(values[item.index] || 0);
                                const pct = total > 0 ? ((value / total) * 100).toFixed(1) : "0.0";
                                return { ...item, text: `${item.text} (${pct}%)` };
                            });
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label(tooltipContext) {
                            const values = tooltipContext.dataset.data || [];
                            const total = values.reduce((sum, value) => sum + Number(value || 0), 0);
                            const value = Number(tooltipContext.parsed || 0);
                            const pct = total > 0 ? ((value / total) * 100).toFixed(1) : "0.0";
                            return `${tooltipContext.label}: ${value} (${pct}%)`;
                        }
                    }
                }
            }
        }
        : {
            indexAxis: "y",
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label(tooltipContext) {
                            const values = tooltipContext.dataset.data || [];
                            const total = values.reduce((sum, value) => sum + Number(value || 0), 0);
                            const value = Number(tooltipContext.parsed?.x ?? tooltipContext.parsed ?? 0);
                            const pct = total > 0 ? ((value / total) * 100).toFixed(1) : "0.0";
                            return `${tooltipContext.dataset.label || tooltipContext.label}: ${value} (${pct}%)`;
                        }
                    }
                }
            },
            scales: {
                x: { beginAtZero: true, grid: ctx.commonGrid, ticks: ctx.commonTicks },
                y: { grid: { display: false }, ticks: ctx.commonTicks }
            }
        };

    new Chart(canvas, {
        type: chartType,
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
        options
    });
}

window.DashboardChartBuilders = {
    ...(window.DashboardChartBuilders || {}),
    createBrowsingChart
};
