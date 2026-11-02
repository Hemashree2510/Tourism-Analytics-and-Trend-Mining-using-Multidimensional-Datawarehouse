/**
 * Clustering Module Client Scripts
 * Handles K-Means execution, scatter visualization, and summary statistics
 */

let clusterChart = null;
let currentClusterData = null;

document.addEventListener('DOMContentLoaded', () => {
    loadClusteringResults();

    const btnRun = document.getElementById('btnRunClustering');
    if (btnRun) {
        btnRun.addEventListener('click', runClustering);
    }

    const searchInput = document.getElementById('clusterTableSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            if (currentClusterData) {
                renderCountriesTable(currentClusterData.countries, e.target.value.trim());
            }
        });
    }
});

async function loadClusteringResults() {
    try {
        const res = await fetch('/api/clustering/results');
        const data = await res.json();
        currentClusterData = data;
        renderClusteringUI(data);
    } catch (err) {
        console.error("Error loading clustering results:", err);
    }
}

async function runClustering() {
    const btn = document.getElementById('btnRunClustering');
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Clustering...`;

    const payload = {
        n_clusters: parseInt(document.getElementById('clusterK').value),
        random_state: parseInt(document.getElementById('clusterRandomState').value)
    };

    try {
        const res = await fetch('/api/clustering/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        currentClusterData = data;
        renderClusteringUI(data);
    } catch (err) {
        alert("Clustering failed: " + err);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-play"></i> Run Clustering`;
    }
}

function renderClusteringUI(data) {
    renderScatterChart(data);
    renderSummaryTable(data.cluster_summaries);
    renderCountriesTable(data.countries, '');
}

function renderScatterChart(data) {
    const ctx = document.getElementById('clusteringScatterChart').getContext('2d');
    if (clusterChart) clusterChart.destroy();

    const clusterColors = ['#4F46E5', '#EC4899', '#F59E0B', '#10B981', '#06B6D4'];

    const datasets = data.cluster_summaries.map((summary, idx) => {
        const cId = summary.cluster_id;
        const pts = data.scatter_all_countries.filter(p => p.cluster === cId).map(p => ({
            x: p.x,
            y: p.y,
            country: p.country
        }));

        return {
            label: `${summary.label} (Mean: ${summary.mean}M, Count: ${summary.count})`,
            data: pts,
            backgroundColor: clusterColors[idx % clusterColors.length],
            pointRadius: 6,
            pointHoverRadius: 9
        };
    });

    clusterChart = new Chart(ctx, {
        type: 'scatter',
        data: { datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            const pt = ctx.raw;
                            return ` ${pt.country}: 2023 Arrivals = ${pt.y}M`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Country Index (Ordered by Arrival Volume)', font: { size: 11 } },
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

function renderSummaryTable(summaries) {
    const tbody = document.getElementById('clusterSummaryTbody');
    const interpList = document.getElementById('clusterInterpretationList');
    tbody.innerHTML = '';
    interpList.innerHTML = '';

    summaries.forEach(s => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${s.label}</strong></td>
            <td>${s.count}</td>
            <td><strong>${s.mean.toFixed(2)}</strong></td>
            <td>${s.min.toFixed(2)}</td>
            <td>${s.max.toFixed(2)}</td>
        `;
        tbody.appendChild(tr);

        const li = document.createElement('li');
        li.innerHTML = `<strong>${s.label} (${s.count} countries):</strong> ${s.tier_description}. Observed range is ${s.min}M to ${s.max}M arrivals.`;
        interpList.appendChild(li);
    });
}

function renderCountriesTable(countries, search = '') {
    const tbody = document.getElementById('clusterCountriesTbody');
    tbody.innerHTML = '';

    let filtered = countries;
    if (search) {
        filtered = filtered.filter(c => c.country.toLowerCase().includes(search.toLowerCase()));
    }

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 20px;">No countries match the search.</td></tr>`;
        return;
    }

    filtered.forEach(c => {
        const tr = document.createElement('tr');
        let badgeClass = 'badge-cluster-0';
        if (c.cluster === 1) badgeClass = 'badge-cluster-1';
        else if (c.cluster === 2) badgeClass = 'badge-cluster-2';

        let tierText = "Tier 3: Developing Destination";
        if (c.arrivals_2023 > 50) tierText = "Tier 1: Global Mega-Hub";
        else if (c.arrivals_2023 >= 18) tierText = "Tier 2: Major Destination";

        tr.innerHTML = `
            <td><strong style="color: var(--text-navy);">${c.country}</strong></td>
            <td>${c.arrivals_2023.toFixed(2)} M</td>
            <td>${c.arrivals_2022 !== null ? c.arrivals_2022.toFixed(2) + ' M' : '<span style="color: #94A3B8;">N/A</span>'}</td>
            <td><span class="badge ${badgeClass}">${c.cluster_name}</span></td>
            <td><span style="font-size: 12px; color: var(--text-secondary);">${tierText}</span></td>
        `;
        tbody.appendChild(tr);
    });
}
