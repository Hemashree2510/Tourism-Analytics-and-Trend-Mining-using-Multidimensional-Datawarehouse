/**
 * TourismVista Dashboard Visualizations & Data Binding
 * Professional academic aesthetics, Chart.js, Leaflet map, and real API integrations
 */

document.addEventListener('DOMContentLoaded', () => {
    initFilters();
    loadDashboardKPIs();
    loadCharts();
    loadMap();
    loadTopCountriesTable();
    setupEventListeners();
});

// Chart instances store
let charts = {};
let leafletMap = null;
let mapMarkers = [];

// Country coordinate lookup for Leaflet map markers
const countryCoordinates = {
    "France": [46.2276, 2.2137],
    "Spain": [40.4637, -3.7492],
    "United States": [37.0902, -95.7129],
    "Italy": [41.8719, 12.5674],
    "Turkey": [38.9637, 35.2433],
    "Mexico": [23.6345, -102.5528],
    "United Kingdom": [55.3781, -3.4360],
    "Germany": [51.1657, 10.4515],
    "Greece": [39.0742, 21.8243],
    "Austria": [47.5162, 14.5501],
    "Thailand": [15.8700, 100.9925],
    "Saudi Arabia": [23.8859, 45.0792],
    "United Arab Emirates": [23.4241, 53.8478],
    "Portugal": [39.3999, -8.2245],
    "Japan": [36.2048, 138.2529],
    "Netherlands": [52.1326, 5.2913],
    "Poland": [51.9194, 19.1451],
    "Canada": [56.1304, -106.3468],
    "Egypt": [26.8206, 30.8025],
    "Morocco": [31.7917, -7.0926],
    "China": [35.8617, 104.1954],
    "India": [20.5937, 78.9629],
    "Brazil": [-14.2350, -51.9253],
    "South Korea": [35.9078, 127.7669],
    "Vietnam": [14.0583, 108.2772],
    "South Africa": [-30.5595, 22.9375],
    "Indonesia": [-0.7893, 113.9213],
    "Australia": [-25.2744, 133.7751],
    "Switzerland": [46.8182, 8.2275],
    "Malaysia": [4.2105, 101.9758],
    "Croatia": [45.1000, 15.2000],
    "Denmark": [56.2639, 9.5018],
    "Norway": [60.4720, 8.4689],
    "Sweden": [60.1282, 18.6435],
    "Argentina": [-38.4161, -63.6167],
    "Chile": [-35.6751, -71.5430],
    "Colombia": [4.5709, -74.2973],
    "Peru": [-9.1900, -75.0152],
    "Singapore": [1.3521, 103.8198],
    "New Zealand": [-40.9006, 174.8860]
};

// ============================================================
// 1. FILTERS INITIALIZATION
// ============================================================
async function initFilters() {
    try {
        const res = await fetch('/api/countries');
        const data = await res.json();
        const countrySelect = document.getElementById('filterCountry');
        data.countries.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c;
            opt.textContent = c;
            countrySelect.appendChild(opt);
        });
    } catch (err) {
        console.error("Error loading country filter list:", err);
    }
}

// ============================================================
// 2. DASHBOARD KPIS
// ============================================================
async function loadDashboardKPIs(filters = {}) {
    const query = new URLSearchParams(filters).toString();
    try {
        const res = await fetch(`/api/summary?${query}`);
        const data = await res.json();

        // Update DOM
        document.getElementById('kpiTotalCountries').textContent = data.total_countries;
        document.getElementById('kpiCountries2023').textContent = data.countries_2023_data;
        
        if (data.highest_country && data.highest_country.country !== 'N/A') {
            document.getElementById('kpiHighestCountry').textContent = data.highest_country.country;
            document.getElementById('kpiHighestValue').textContent = `${data.highest_country.arrivals} M`;
        } else {
            document.getElementById('kpiHighestCountry').textContent = 'N/A';
            document.getElementById('kpiHighestValue').textContent = '0 M';
        }

        if (data.yoy_comparison.available) {
            document.getElementById('kpiYoYGrowth').textContent = `+${data.yoy_comparison.growth_pct}%`;
            document.getElementById('kpiYoYNote').textContent = `${data.yoy_comparison.countries_count} comparable countries`;
        } else {
            document.getElementById('kpiYoYGrowth').textContent = 'N/A';
            document.getElementById('kpiYoYNote').textContent = data.yoy_comparison.note;
        }

        document.getElementById('kpiPredictedTotal').textContent = `${data.predicted_2024.total_millions.toLocaleString()} M`;
        document.getElementById('kpiPredictedCount').textContent = `Across ${data.predicted_2024.count} forecast countries (Mean: ${data.predicted_2024.average_millions}M)`;

    } catch (err) {
        console.error("Error loading KPIs:", err);
    }
}

// ============================================================
// 3. CHARTS RENDERING
// ============================================================
async function loadCharts() {
    try {
        const [trendsRes, clusterRes] = await Promise.all([
            fetch('/api/tourism/trends'),
            fetch('/api/clustering/results')
        ]);
        const trends = await trendsRes.json();
        const clusters = await clusterRes.json();

        renderArrivalTrendChart(trends.yearly_aggregates);
        renderTopCountriesChart(trends.top_countries_2023);
        renderComparisonChart(trends.comparison_2022_2023);
        renderCategoryDoughnut(trends.category_distribution);
        renderClustersChart(clusters);
        renderWorldBankChart(trends.world_bank_historical);

    } catch (err) {
        console.error("Error loading charts:", err);
    }
}

// Chart 1: Arrival Trends Line Chart
function renderArrivalTrendChart(aggregates) {
    const ctx = document.getElementById('chartArrivalTrend').getContext('2d');
    if (charts.arrivalTrend) charts.arrivalTrend.destroy();

    charts.arrivalTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['2022 (Actual)', '2023 (Actual)', '2024 (Predicted)'],
            datasets: [{
                label: 'Total Arrivals (Millions)',
                data: [
                    aggregates['2022_actual'].total_millions,
                    aggregates['2023_actual'].total_millions,
                    aggregates['2024_pred'].total_millions
                ],
                borderColor: '#2563EB',
                backgroundColor: 'rgba(37, 99, 235, 0.08)',
                fill: true,
                tension: 0.3,
                pointBackgroundColor: ['#3B82F6', '#10B981', '#F59E0B'],
                pointBorderColor: '#FFFFFF',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
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
                            return ` Total: ${ctx.parsed.y} Million arrivals`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: { color: '#F1F5F9' },
                    ticks: { callback: val => `${val}M` }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

// Chart 2: Top 10 Countries Bar Chart
function renderTopCountriesChart(topData) {
    const ctx = document.getElementById('chartTopCountries').getContext('2d');
    if (charts.topCountries) charts.topCountries.destroy();

    charts.topCountries = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topData.labels,
            datasets: [{
                label: '2023 Arrivals (Millions)',
                data: topData.data,
                backgroundColor: '#3B82F6',
                borderRadius: 6,
                hoverBackgroundColor: '#1D4ED8'
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.parsed.x} Million arrivals`
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: '#F1F5F9' },
                    ticks: { callback: val => `${val}M` }
                },
                y: {
                    grid: { display: false }
                }
            }
        }
    });
}

// Chart 3: 2022 vs 2023 Comparison
function renderComparisonChart(compData) {
    const ctx = document.getElementById('chartComparison').getContext('2d');
    if (charts.comparison) charts.comparison.destroy();

    // Show top 8 comparable countries for clean chart spacing
    const sliceCount = 8;
    const labels = compData.labels.slice(0, sliceCount);
    const d22 = compData.data_2022.slice(0, sliceCount);
    const d23 = compData.data_2023.slice(0, sliceCount);

    charts.comparison = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '2022 Actual',
                    data: d22,
                    backgroundColor: '#93C5FD',
                    borderRadius: 4
                },
                {
                    label: '2023 Actual',
                    data: d23,
                    backgroundColor: '#2563EB',
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y}M`
                    }
                }
            },
            scales: {
                y: {
                    grid: { color: '#F1F5F9' },
                    ticks: { callback: val => `${val}M` }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

// Chart 4: Tourism Arrival Categories Doughnut
function renderCategoryDoughnut(categories) {
    const ctx = document.getElementById('chartCategoryDoughnut').getContext('2d');
    if (charts.categoryDoughnut) charts.categoryDoughnut.destroy();

    const labels = ['High Tourism (>50M)', 'Medium Tourism (20-50M)', 'Low Tourism (<20M)'];
    const counts = [
        categories['High Tourism'] || 0,
        categories['Medium Tourism'] || 0,
        categories['Low Tourism'] || 0
    ];

    charts.categoryDoughnut = new Chart(ctx, {
        type: 'doughnut',
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
            cutout: '68%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { boxWidth: 12, font: { size: 11 }, padding: 12 }
                },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            const val = ctx.parsed;
                            const total = counts.reduce((a, b) => a + b, 0);
                            const pct = ((val / total) * 100).toFixed(1);
                            return ` ${ctx.label}: ${val} countries (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Chart 5: K-Means Country Clusters Scatter Plot
function renderClustersChart(clusterRes) {
    const ctx = document.getElementById('chartClusters').getContext('2d');
    if (charts.clusters) charts.clusters.destroy();

    const clusterColors = ['#4F46E5', '#EC4899', '#F59E0B'];

    // Group scatter points by cluster
    const datasets = [0, 1, 2].map(cId => {
        const summary = clusterRes.cluster_summaries.find(s => s.cluster_id === cId) || {};
        const points = clusterRes.scatter_both_years.filter(p => p.cluster === cId).map(p => ({
            x: p.x,
            y: p.y,
            country: p.country
        }));

        return {
            label: `Cluster ${cId} (${summary.count || points.length} countries)`,
            data: points,
            backgroundColor: clusterColors[cId],
            pointRadius: 6,
            pointHoverRadius: 9
        };
    });

    charts.clusters = new Chart(ctx, {
        type: 'scatter',
        data: { datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 10, font: { size: 10 } } },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            const pt = ctx.raw;
                            return ` ${pt.country}: 2022 = ${pt.x}M, 2023 = ${pt.y}M`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: '2022 Tourist Arrivals (Millions)', font: { size: 11 } },
                    grid: { color: '#F1F5F9' }
                },
                y: {
                    title: { display: true, text: '2023 Tourist Arrivals (Millions)', font: { size: 11 } },
                    grid: { color: '#F1F5F9' }
                }
            }
        }
    });
}

// Chart 7: World Bank Historical Bar Chart
function renderWorldBankChart(wbData) {
    const ctx = document.getElementById('chartWorldBank').getContext('2d');
    if (charts.worldBank) charts.worldBank.destroy();

    charts.worldBank = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: wbData.years.map(String),
            datasets: [{
                label: 'Reporting Countries Count',
                data: wbData.counts,
                backgroundColor: '#EA580C',
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
                        label: ctx => ` Reporting: ${ctx.parsed.y} countries`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#F1F5F9' },
                    title: { display: true, text: 'Countries', font: { size: 10 } }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

// ============================================================
// 4. LEAFLET MAP
// ============================================================
async function loadMap() {
    const mapContainer = document.getElementById('tourismMap');
    if (!mapContainer) return;

    if (!leafletMap) {
        leafletMap = L.map('tourismMap').setView([25.0, 10.0], 2);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 18,
            attribution: '© OpenStreetMap contributors'
        }).addTo(leafletMap);
    }

    // Clear existing markers
    mapMarkers.forEach(m => leafletMap.removeLayer(m));
    mapMarkers = [];

    try {
        const res = await fetch('/api/tourism/top-countries?year=2023&limit=50');
        const data = await res.json();

        data.records.forEach(r => {
            const coords = countryCoordinates[r.country];
            if (coords) {
                const arr = r.selected_year_arrival || 0;
                let color = '#F59E0B'; // Low
                if (arr > 50) color = '#10B981'; // High
                else if (arr >= 20) color = '#3B82F6'; // Medium

                const radius = Math.min(Math.max(arr * 0.35, 6), 28);

                const circle = L.circleMarker(coords, {
                    radius: radius,
                    fillColor: color,
                    color: '#FFFFFF',
                    weight: 1.5,
                    opacity: 1,
                    fillOpacity: 0.75
                }).addTo(leafletMap);

                circle.bindPopup(`
                    <div style="font-family: 'Inter', sans-serif; font-size: 12px; padding: 4px;">
                        <strong style="color: #1E3A8A; font-size: 13px;">${r.country}</strong><br>
                        <span>2023 Arrivals: <b>${arr} Million</b></span><br>
                        <span>Classification: <b>${r.category}</b></span><br>
                        <a href="/country-analysis?country=${encodeURIComponent(r.country)}" style="display: inline-block; margin-top: 6px; color: #2563EB; font-weight: 600;">View Detailed Analysis →</a>
                    </div>
                `);

                mapMarkers.push(circle);
            }
        });
    } catch (err) {
        console.error("Error loading map markers:", err);
    }
}

// ============================================================
// 5. TOP COUNTRIES TABLE
// ============================================================
async function loadTopCountriesTable(year = 2023, search = "") {
    try {
        const res = await fetch(`/api/tourism/top-countries?year=${year}&search=${encodeURIComponent(search)}&limit=15`);
        const data = await res.json();
        const tbody = document.getElementById('topCountriesTbody');
        tbody.innerHTML = '';

        if (!data.records || data.records.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 24px;">No countries match your search query.</td></tr>`;
            return;
        }

        data.records.forEach(r => {
            const tr = document.createElement('tr');
            
            let badgeClass = 'badge-low';
            if (r.category === 'High Tourism') badgeClass = 'badge-high';
            else if (r.category === 'Medium Tourism') badgeClass = 'badge-medium';

            tr.innerHTML = `
                <td style="font-weight: 600; color: var(--text-muted);">${r.rank}</td>
                <td>
                    <strong style="color: var(--text-navy);">${r.country}</strong>
                </td>
                <td>${r.arrivals_2022 !== null ? r.arrivals_2022.toFixed(2) : '<span style="color: #94A3B8;">N/A</span>'}</td>
                <td>${r.arrivals_2023 !== null ? r.arrivals_2023.toFixed(2) : '<span style="color: #94A3B8;">N/A</span>'}</td>
                <td>${r.arrivals_2024_pred !== null ? r.arrivals_2024_pred.toFixed(2) : '<span style="color: #94A3B8;">N/A</span>'}</td>
                <td><span class="badge ${badgeClass}">${r.category}</span></td>
                <td>
                    <a href="/country-analysis?country=${encodeURIComponent(r.country)}" class="btn btn-outline" style="height: 28px; padding: 0 10px; font-size: 11px;">
                        Analyze <i class="fa-solid fa-arrow-right"></i>
                    </a>
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch (err) {
        console.error("Error loading top countries table:", err);
    }
}

// ============================================================
// 6. EVENT LISTENERS
// ============================================================
function setupEventListeners() {
    const btnApply = document.getElementById('btnApplyFilters');
    const btnReset = document.getElementById('btnResetFilters');
    const searchInput = document.getElementById('tableSearch');

    btnApply.addEventListener('click', () => {
        const filters = {
            year: document.getElementById('filterYear').value,
            country: document.getElementById('filterCountry').value,
            data_type: document.getElementById('filterDataType').value,
            category: document.getElementById('filterCategory').value
        };
        loadDashboardKPIs(filters);
        const selYear = filters.year === 'All' ? 2023 : parseInt(filters.year);
        loadTopCountriesTable(selYear, searchInput.value.trim());
    });

    btnReset.addEventListener('click', () => {
        document.getElementById('filterYear').value = '2023';
        document.getElementById('filterCountry').value = 'All';
        document.getElementById('filterDataType').value = 'All';
        document.getElementById('filterCategory').value = 'All';
        searchInput.value = '';
        loadDashboardKPIs({});
        loadTopCountriesTable(2023, '');
    });

    searchInput.addEventListener('input', (e) => {
        const yr = parseInt(document.getElementById('filterYear').value) || 2023;
        loadTopCountriesTable(yr, e.target.value.trim());
    });
}
