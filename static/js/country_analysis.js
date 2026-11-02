/**
 * Country Analysis Module Client Scripts
 */

let countryProgressionChart = null;

document.addEventListener('DOMContentLoaded', async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const initialCountry = urlParams.get('country') || 'France';

    await populateCountrySelect(initialCountry);
    loadCountryData(initialCountry);

    document.getElementById('countrySelect').addEventListener('change', (e) => {
        loadCountryData(e.target.value);
    });
});

async function populateCountrySelect(selectedCountry) {
    try {
        const res = await fetch('/api/countries');
        const data = await res.json();
        const select = document.getElementById('countrySelect');
        select.innerHTML = '';

        data.countries.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c;
            opt.textContent = c;
            if (c.toLowerCase() === selectedCountry.toLowerCase()) {
                opt.selected = true;
            }
            select.appendChild(opt);
        });
    } catch (err) {
        console.error("Error populating countries dropdown:", err);
    }
}

async function loadCountryData(country) {
    try {
        const res = await fetch(`/api/country/${encodeURIComponent(country)}`);
        if (!res.ok) {
            alert(`Could not load data for ${country}`);
            return;
        }
        const data = await res.json();

        // Cards
        document.getElementById('card2022').textContent = data.arrivals_2022 !== null ? `${data.arrivals_2022.toFixed(2)} M` : 'N/A';
        document.getElementById('card2023').textContent = data.arrivals_2023 !== null ? `${data.arrivals_2023.toFixed(2)} M` : 'N/A';
        document.getElementById('card2024').textContent = data.arrivals_2024_pred !== null ? `${data.arrivals_2024_pred.toFixed(2)} M` : 'N/A';
        document.getElementById('cardCategory').textContent = data.category;
        document.getElementById('cardCluster').textContent = data.cluster_name || (data.cluster !== undefined ? `Cluster ${data.cluster}` : 'N/A');

        // World Bank
        if (data.worldbank_arrivals !== null) {
            document.getElementById('wbArrivals').textContent = `${(data.worldbank_arrivals / 1e6).toFixed(2)} M (${data.worldbank_arrivals.toLocaleString()})`;
            document.getElementById('wbYear').textContent = `Reference Year: ${data.worldbank_year || 'Historical'}`;
        } else {
            document.getElementById('wbArrivals').textContent = 'N/A';
            document.getElementById('wbYear').textContent = 'No World Bank record available';
        }

        // YoY Change
        if (data.yoy_change_pct !== null) {
            const prefix = data.yoy_change_pct >= 0 ? '+' : '';
            document.getElementById('yoyChange').textContent = `${prefix}${data.yoy_change_pct}%`;
            document.getElementById('yoyExplanation').textContent = `From ${data.arrivals_2022}M (2022) to ${data.arrivals_2023}M (2023).`;
        } else {
            document.getElementById('yoyChange').textContent = 'N/A';
            document.getElementById('yoyExplanation').textContent = 'Requires both 2022 and 2023 actual figures.';
        }

        // Update Chart
        document.getElementById('countryChartTitle').textContent = `${data.country} — Available Observations`;
        renderCountryChart(data);

    } catch (err) {
        console.error("Error loading country data:", err);
    }
}

function renderCountryChart(data) {
    const ctx = document.getElementById('countryProgressionChart').getContext('2d');
    if (countryProgressionChart) countryProgressionChart.destroy();

    const labels = [];
    const values = [];
    const colors = [];

    if (data.arrivals_2022 !== null) {
        labels.push('2022 Actual');
        values.push(data.arrivals_2022);
        colors.push('#93C5FD');
    }
    if (data.arrivals_2023 !== null) {
        labels.push('2023 Actual');
        values.push(data.arrivals_2023);
        colors.push('#2563EB');
    }
    if (data.arrivals_2024_pred !== null) {
        labels.push('2024 Predicted');
        values.push(data.arrivals_2024_pred);
        colors.push('#F59E0B');
    }
    if (data.worldbank_arrivals_millions !== null && data.worldbank_year) {
        labels.push(`World Bank (${data.worldbank_year})`);
        values.push(data.worldbank_arrivals_millions);
        colors.push('#EA580C');
    }

    if (labels.length === 0) {
        labels.push('No Valid Observations');
        values.push(0);
        colors.push('#CBD5E1');
    }

    countryProgressionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Arrivals (Millions)',
                data: values,
                backgroundColor: colors,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.parsed.y} Million arrivals`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
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
