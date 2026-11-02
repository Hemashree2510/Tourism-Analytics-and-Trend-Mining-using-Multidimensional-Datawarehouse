/**
 * OLAP Analysis Module Client Scripts
 * Handles dynamic SQL execution, cube slicing/dicing/pivoting, and table rendering
 */

let currentTab = 'rollup';

document.addEventListener('DOMContentLoaded', () => {
    setupTabNavigation();
    loadTab('rollup');
});

function setupTabNavigation() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentTab = btn.getAttribute('data-tab');
            loadTab(currentTab);
        });
    });
}

function loadTab(tab) {
    const controls = document.getElementById('olapControlsContainer');

    if (tab === 'rollup') {
        controls.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 13px; color: var(--text-secondary);">
                    <strong>Operation:</strong> Aggregates tourist arrivals by year across all dimensions.
                </span>
                <button class="btn btn-primary" onclick="fetchRollup()">
                    <i class="fa-solid fa-play"></i> Run Roll-Up Query
                </button>
            </div>
        `;
        fetchRollup();
    } else if (tab === 'drilldown') {
        controls.innerHTML = `
            <div style="display: flex; flex-wrap: wrap; align-items: flex-end; gap: 16px;">
                <div class="filter-group" style="min-width: 160px;">
                    <label class="filter-label">Drill-Down Target Year</label>
                    <select id="olapDrillYear" class="form-select">
                        <option value="2023" selected>2023 (49 Countries)</option>
                        <option value="2022">2022 (20 Countries)</option>
                        <option value="2024">2024 (50 Countries Predicted)</option>
                        <option value="2019">2019 (World Bank)</option>
                        <option value="2020">2020 (World Bank)</option>
                    </select>
                </div>
                <div>
                    <button class="btn btn-primary" onclick="fetchDrilldown()">
                        <i class="fa-solid fa-play"></i> Execute Drill-Down
                    </button>
                </div>
            </div>
        `;
        fetchDrilldown();
    } else if (tab === 'slice') {
        controls.innerHTML = `
            <div style="display: flex; flex-wrap: wrap; align-items: flex-end; gap: 16px;">
                <div class="filter-group" style="min-width: 160px;">
                    <label class="filter-label">Slice Time Dimension</label>
                    <select id="olapSliceYear" class="form-select">
                        <option value="2023" selected>Year = 2023 (Actual Kaggle)</option>
                        <option value="2022">Year = 2022 (Actual Kaggle)</option>
                    </select>
                </div>
                <div class="filter-group" style="min-width: 200px;">
                    <label class="filter-label">Fixed Tourism Type</label>
                    <input type="text" class="form-control" value="Actual Arrivals (Type Key = 1)" disabled style="background: #F1F5F9;">
                </div>
                <div>
                    <button class="btn btn-primary" onclick="fetchSlice()">
                        <i class="fa-solid fa-play"></i> Execute Slice
                    </button>
                </div>
            </div>
        `;
        fetchSlice();
    } else if (tab === 'dice') {
        controls.innerHTML = `
            <div style="display: flex; flex-wrap: wrap; align-items: flex-end; gap: 16px;">
                <div class="filter-group" style="min-width: 220px;">
                    <label class="filter-label">Target Countries Subset</label>
                    <input type="text" id="olapDiceCountries" class="form-control" value="United States, France, Spain, Germany, Mexico">
                </div>
                <div class="filter-group" style="min-width: 160px;">
                    <label class="filter-label">Target Years Subset</label>
                    <input type="text" id="olapDiceYears" class="form-control" value="2022, 2023, 2024">
                </div>
                <div>
                    <button class="btn btn-primary" onclick="fetchDice()">
                        <i class="fa-solid fa-play"></i> Execute Dice Sub-Cube
                    </button>
                </div>
            </div>
        `;
        fetchDice();
    } else if (tab === 'pivot') {
        controls.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 13px; color: var(--text-secondary);">
                    <strong>Operation:</strong> Transposes years (2022, 2023, 2024 predicted) into cross-tabular matrix columns.
                </span>
                <button class="btn btn-primary" onclick="fetchPivot()">
                    <i class="fa-solid fa-play"></i> Run Pivot Cross-Tab
                </button>
            </div>
        `;
        fetchPivot();
    }
}

async function fetchRollup() {
    renderLoading();
    try {
        const res = await fetch('/api/olap/rollup');
        const data = await res.json();
        renderOlapResult(data);
    } catch (err) {
        renderError(err);
    }
}

async function fetchDrilldown() {
    renderLoading();
    const yr = document.getElementById('olapDrillYear') ? document.getElementById('olapDrillYear').value : 2023;
    try {
        const res = await fetch(`/api/olap/drilldown?year=${yr}`);
        const data = await res.json();
        renderOlapResult(data);
    } catch (err) {
        renderError(err);
    }
}

async function fetchSlice() {
    renderLoading();
    const yr = document.getElementById('olapSliceYear') ? document.getElementById('olapSliceYear').value : 2023;
    try {
        const res = await fetch(`/api/olap/slice?year=${yr}`);
        const data = await res.json();
        renderOlapResult(data);
    } catch (err) {
        renderError(err);
    }
}

async function fetchDice() {
    renderLoading();
    const cVal = document.getElementById('olapDiceCountries') ? document.getElementById('olapDiceCountries').value : "United States, France, Spain";
    const yVal = document.getElementById('olapDiceYears') ? document.getElementById('olapDiceYears').value : "2022, 2023, 2024";

    const countries = cVal.split(',').map(s => s.trim()).filter(Boolean);
    const years = yVal.split(',').map(s => parseInt(s.trim())).filter(Boolean);

    try {
        const res = await fetch('/api/olap/dice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ countries, years })
        });
        const data = await res.json();
        renderOlapResult(data);
    } catch (err) {
        renderError(err);
    }
}

async function fetchPivot() {
    renderLoading();
    try {
        const res = await fetch('/api/olap/pivot');
        const data = await res.json();
        renderOlapResult(data);
    } catch (err) {
        renderError(err);
    }
}

function renderLoading() {
    document.getElementById('olapExecutionTime').textContent = "Executing...";
    document.getElementById('olapTableTbody').innerHTML = `
        <tr><td colspan="10" style="text-align: center; padding: 24px; color: var(--text-muted);">
            <i class="fa-solid fa-spinner fa-spin" style="margin-right: 6px;"></i> Executing SQL query against warehouse...
        </td></tr>
    `;
}

function renderError(err) {
    document.getElementById('olapExecutionTime').textContent = "Error";
    document.getElementById('olapTableTbody').innerHTML = `
        <tr><td colspan="10" style="text-align: center; padding: 24px; color: #B91C1C;">
            <i class="fa-solid fa-circle-exclamation" style="margin-right: 6px;"></i> Error executing query: ${err}
        </td></tr>
    `;
}

function renderOlapResult(data) {
    document.getElementById('olapSqlCode').textContent = data.sql_query;
    document.getElementById('olapExecutionTime').textContent = `${data.duration_ms} ms`;
    document.getElementById('olapResultTitle').textContent = data.title;
    document.getElementById('olapResultCount').textContent = `${data.rows.length} rows returned`;

    const thead = document.getElementById('olapTableThead');
    const tbody = document.getElementById('olapTableTbody');

    thead.innerHTML = '';
    tbody.innerHTML = '';

    // Headers
    const trHead = document.createElement('tr');
    data.columns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col.replace(/_/g, ' ');
        trHead.appendChild(th);
    });
    thead.appendChild(trHead);

    // Rows
    if (data.rows.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${data.columns.length}" style="text-align: center; color: var(--text-muted); padding: 20px;">No rows returned for the selected slice.</td></tr>`;
        return;
    }

    data.rows.forEach(r => {
        const tr = document.createElement('tr');
        data.columns.forEach(col => {
            const td = document.createElement('td');
            const val = r[col];
            if (val === null || val === undefined) {
                td.innerHTML = '<span style="color: #94A3B8;">N/A</span>';
            } else {
                td.textContent = val;
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
}
