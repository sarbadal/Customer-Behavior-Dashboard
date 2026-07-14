function createDeviceChart(ctx, config = {}) {
    const canvas = document.getElementById("deviceChart");
    if (!canvas) {
        return;
    }

    const chartType = config.type || "doughnut";
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
            layout: {
                padding: {
                    right: ctx.isNarrow ? 0 : 8
                }
            },
            plugins: {
                legend: {
                    position: ctx.isNarrow ? "bottom" : "right",
                    labels: {
                        boxWidth: 16,
                        boxHeight: 16,
                        padding: 14,
                        font: {
                            size: ctx.legendFontSize
                        },
                        generateLabels(chart) {
                            const chartOverrides = Chart.overrides[chart.config.type] || {};
                            const baseGenerateLabels =
                                chartOverrides?.plugins?.legend?.labels?.generateLabels ||
                                Chart.overrides.doughnut.plugins.legend.labels.generateLabels;

                            const original = baseGenerateLabels(chart);
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
                        label(context) {
                            const values = context.dataset.data || [];
                            const total = values.reduce((sum, value) => sum + Number(value || 0), 0);
                            const value = Number(context.parsed || 0);
                            const pct = total > 0 ? ((value / total) * 100).toFixed(1) : "0.0";
                            return `${context.label}: ${value} (${pct}%)`;
                        }
                    }
                }
            }
        }
        : {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label(context) {
                            const values = context.dataset.data || [];
                            const total = values.reduce((sum, value) => sum + Number(value || 0), 0);
                            const value = Number(context.parsed?.y ?? context.parsed ?? 0);
                            const pct = total > 0 ? ((value / total) * 100).toFixed(1) : "0.0";
                            return `${context.label}: ${value} (${pct}%)`;
                        }
                    }
                }
            }
        };

    new Chart(canvas, {
        type: chartType,
        data: {
            labels: ctx.deviceLabels,
            datasets: [{
                label: "Devices",
                data: ctx.deviceValues,
                backgroundColor: ["#0f766e", "#1d4ed8", "#f59e0b", "#ef4444", "#10b981", "#3b82f6", "#f97316"],
                borderRadius: 8,
                maxBarThickness: 38,
                borderWidth: 2,
                borderColor: "#f7f8f5"
            }]
        },
        options
    });
}

window.DashboardChartBuilders = {
    ...(window.DashboardChartBuilders || {}),
    createDeviceChart
};
