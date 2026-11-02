/**
 * Tourism Trends Module Client Scripts
 */

let diffChart = null;
let distChart = null;

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const [trendsRes, top2024Res] = await Promise.all([
            fetch('/api/tourism/trends'),
            fetch('/api/tourism/top-countries?year=2024&limit=15')
        ]);
        const trends = await trendsRes.json();
        const top2024 = await top2024Res.json();

        renderDifferencesChart(trends.comparison_2022_2023);
        renderCategoryDistChart(trends.category_distribution);
        renderPredictedTable(top2024.records);
    } catch (err) {
        console.error("Error loading trends:", err);
    }
});

function renderDifferencesChart(compData) {
    const ctx = document.getElementById('chartYoYDifferences').getContext('2d');
    if (diffChart) diffChart.destroy();

    // Compute diffs
    const diffs = [];
    for (let i = 0; i < compData.labels.length; i++) {
        const country = compData.labels[i];
        const v22 = compData.data_2022[i];
        const v23 = compData.data_2023[i];
        const diff = +(v23 - v22).toFixed(2);
        diffs.push({ country, diff, v22, v23 });
    }

    diffs.sort((a, b) => b.diff - a.diff);

    const labels = diffs.map(d => d.country);
    const values = diffs.map(d => d.diff);
    const colors = values.map(v => v >= 0 ? '#10B981' : '#EF4444');

    diffChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'YoY Absolute Arrival Difference (M)',
                data: values,
                backgroundColor: colors,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            const d = diffs[ctx.dataIndex];
                            const sign = d.diff >= 0 ? '+' : '';
                            return ` Change: ${sign}${d.diff}M (From ${d.v22}M in 2022 to ${d.v23}M in 2023)`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    grid: { color: '#F1F5F9' },
                    ticks: { callback: val => `${val}M` }
                },
                x: {
                    grid: { display: false },
                    ticks: { maxRotation: 45, minRotation: 45, font: { size: 10 } }
                }
            }
        }
    });
}

function renderCategoryDistChart(dist) {
    const ctx = document.getElementById('chartCategoryDist').getContext('2d');
    if (distChart) distChart.destroy();

    const labels = ['High Tourism', 'Medium Tourism', 'Low Tourism'];
    const counts = [
        dist['High Tourism'] || 0,
        dist['Medium Tourism'] || 0,
        dist['Low Tourism'] || 0
    ];

    distChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: ['#10B981', '#3B82F6', '#F59E0B'],
                borderWidth: 2,
                borderColor: '#FFFFFF'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 }, padding: 12 } }
            }
        }
    });
}

function renderPredictedTable(records) {
    const tbody = document.getElementById('tbodyPredictedLeaders');
    tbody.innerHTML = '';

    records.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>#${r.rank}</strong></td>
            <td><strong style="color: var(--text-navy);">${r.country}</strong></td>
            <td><strong style="color: var(--accent-orange);">${r.arrivals_2024_pred.toFixed(2)} M</strong></td>
            <td>${r.arrivals_2023 !== null ? r.arrivals_2023.toFixed(2) + ' M' : '<span style="color: #94A3B8;">N/A</span>'}</td>
            <td>${r.arrivals_2022 !== null ? r.arrivals_2022.toFixed(2) + ' M' : '<span style="color: #94A3B8;">N/A</span>'}</td>
            <td><span class="badge badge-low">Forecast Projections</span></td>
        `;
        tbody.appendChild(tr);
    });
}
