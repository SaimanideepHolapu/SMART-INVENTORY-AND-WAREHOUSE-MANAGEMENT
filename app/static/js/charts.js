// Chart.js integrations for Dashboard and Analytics

document.addEventListener('DOMContentLoaded', function() {
    // Check if dashboard charts exist
    const flowCanvas = document.getElementById('stockFlowChart');
    const catCanvas = document.getElementById('categoryChart');

    if (flowCanvas && catCanvas) {
        fetch('/api/dashboard/chart-data')
            .then(res => res.json())
            .then(data => {
                renderDashboardCharts(data);
            })
            .catch(err => console.error('Error fetching dashboard chart data:', err));
    }

    // Check if analytics charts exist
    const analyticsTrends = document.getElementById('analyticsTrendsChart');
    const healthCanvas = document.getElementById('healthChart');

    if (analyticsTrends && healthCanvas) {
        fetch('/api/analytics/charts')
            .then(res => res.json())
            .then(data => {
                renderAnalyticsCharts(data);
            })
            .catch(err => console.error('Error fetching analytics chart data:', err));
    }
});

function renderDashboardCharts(data) {
    // 1. Stock In vs Stock Out Flow Chart
    const flowCtx = document.getElementById('stockFlowChart').getContext('2d');
    new Chart(flowCtx, {
        type: 'bar',
        data: {
            labels: data.trends.labels,
            datasets: [
                {
                    label: 'Stock In (Received)',
                    data: data.trends.stock_in,
                    backgroundColor: 'rgba(59, 130, 246, 0.85)',
                    borderColor: '#2563eb',
                    borderWidth: 1,
                    borderRadius: 4
                },
                {
                    label: 'Stock Out (Dispatched)',
                    data: data.trends.stock_out,
                    backgroundColor: 'rgba(244, 63, 94, 0.85)',
                    borderColor: '#e11d48',
                    borderWidth: 1,
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            return `${ctx.dataset.label}: ${ctx.raw} units`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { precision: 0 }
                }
            }
        }
    });

    // 2. Category Breakdown Doughnut Chart
    const catCtx = document.getElementById('categoryChart').getContext('2d');
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#64748b'];

    new Chart(catCtx, {
        type: 'doughnut',
        data: {
            labels: data.categories.labels,
            datasets: [{
                data: data.categories.units,
                backgroundColor: colors.slice(0, data.categories.labels.length),
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 12 } }
            },
            cutout: '68%'
        }
    });
}

function renderAnalyticsCharts(data) {
    // 1. 14-day trend line chart
    const trendCtx = document.getElementById('analyticsTrendsChart').getContext('2d');
    new Chart(trendCtx, {
        type: 'line',
        data: {
            labels: data.trends.labels,
            datasets: [
                {
                    label: 'Units In',
                    data: data.trends.stock_in,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    fill: true,
                    tension: 0.35,
                    borderWidth: 2
                },
                {
                    label: 'Units Out',
                    data: data.trends.stock_out,
                    borderColor: '#e11d48',
                    backgroundColor: 'rgba(225, 29, 72, 0.1)',
                    fill: true,
                    tension: 0.35,
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0 } }
            }
        }
    });

    // 2. Health Distribution Pie Chart
    const healthCtx = document.getElementById('healthChart').getContext('2d');
    new Chart(healthCtx, {
        type: 'pie',
        data: {
            labels: ['In Stock (Healthy)', 'Low Stock (Reorder)', 'Out of Stock (Depleted)'],
            datasets: [{
                data: data.health,
                backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}
