function createCityChart(ctx, config = {}) {
    const canvas = document.getElementById("cityChart");
    if (!canvas) {
        return;
    }

    const chartType = config.type || "polarArea";
    const circularTypes = new Set(["doughnut", "pie", "polarArea", "radar"]);
    const usesRadialScale = chartType === "polarArea" || chartType === "radar";
    const isCircular = circularTypes.has(chartType);

    if (isCircular) {
        canvas.style.removeProperty("aspect-ratio");
        canvas.style.setProperty("height", ctx.isNarrow ? "220px" : "240px", "important");
    } else {
        canvas.style.removeProperty("aspect-ratio");
        canvas.style.removeProperty("height");
    }

    const options = {
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
                maxWidth: ctx.isNarrow ? undefined : 150,
                labels: {
                    boxWidth: 12,
                    boxHeight: 12,
                    padding: 10,
                    font: {
                        size: 12
                    },
                    generateLabels(chart) {
                        if (!isCircular) {
                            return Chart.defaults.plugins.legend.labels.generateLabels(chart);
                        }

                        const chartOverrides = Chart.overrides[chart.config.type] || {};
                        const baseGenerateLabels =
                            chartOverrides?.plugins?.legend?.labels?.generateLabels ||
                            Chart.overrides.polarArea.plugins.legend.labels.generateLabels;

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
            }
        }
    };

    if (usesRadialScale) {
        options.scales = { r: { grid: ctx.commonGrid } };
    }

    new Chart(canvas, {
        type: chartType,
        data: {
            labels: ctx.cityLabels,
            datasets: [{
                data: ctx.cityValues,
                borderRadius: 8,
                borderWidth: 2,
                borderColor: "rgba(247, 248, 245, 0.9)",
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
        options
    });
}

window.DashboardChartBuilders = {
    ...(window.DashboardChartBuilders || {}),
    createCityChart
};
