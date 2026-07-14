function createDeviceChart(ctx) {
    const canvas = document.getElementById("deviceChart");
    if (!canvas) {
        return;
    }

    new Chart(canvas, {
        type: "doughnut",
        data: {
            labels: ctx.deviceLabels,
            datasets: [{
                data: ctx.deviceValues,
                backgroundColor: ["#0f766e", "#f97316", "#1d4ed8", "#f59e0b"],
                borderWidth: 2,
                borderColor: "#f7f8f5"
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
                            const original = Chart.overrides.doughnut.plugins.legend.labels.generateLabels(chart);
                            const values = chart.data.datasets[0].data;
                            const total = values.reduce((sum, value) => sum + Number(value), 0);

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
                            const dataset = context.dataset.data;
                            const total = dataset.reduce((sum, value) => sum + Number(value), 0);
                            const value = Number(context.parsed || 0);
                            const pct = total > 0 ? ((value / total) * 100).toFixed(1) : "0.0";
                            return `${context.label}: ${value} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}

window.DashboardChartBuilders = {
    ...(window.DashboardChartBuilders || {}),
    createDeviceChart
};
