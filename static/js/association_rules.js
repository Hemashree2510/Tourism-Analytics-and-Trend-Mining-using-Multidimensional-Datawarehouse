/**
 * Association Rules Client Scripts
 * Handles Apriori execution, rule table rendering, and confidence bar chart
 */

let assocChart = null;

document.addEventListener('DOMContentLoaded', () => {
    loadAssociationResults();

    const btnRun = document.getElementById('btnRunAssoc');
    if (btnRun) {
        btnRun.addEventListener('click', runAssociationMining);
    }
});

async function loadAssociationResults() {
    try {
        const res = await fetch('/api/association-rules');
        const data = await res.json();
        renderAssociationUI(data);
    } catch (err) {
        console.error("Error loading association rules:", err);
    }
}

async function runAssociationMining() {
    const btn = document.getElementById('btnRunAssoc');
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Mining...`;

    const payload = {
        min_support: parseFloat(document.getElementById('assocMinSupport').value),
        min_confidence: parseFloat(document.getElementById('assocMinConfidence').value)
    };

    try {
        const res = await fetch('/api/association-rules/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        renderAssociationUI(data);
    } catch (err) {
        alert("Association mining failed: " + err);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-play"></i> Run Association Mining`;
    }
}

function renderAssociationUI(data) {
    document.getElementById('assocRulesCount').textContent = `${data.rules.length} Rules Generated`;
    renderRulesChart(data.rules);
    renderRulesTable(data.rules);
}

function renderRulesChart(rules) {
    const ctx = document.getElementById('assocRulesChart').getContext('2d');
    if (assocChart) assocChart.destroy();

    const labels = rules.map(r => r.rule_text);
    const confidences = rules.map(r => r.confidence * 100);

    assocChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Confidence (%)',
                data: confidences,
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
                        label: function(ctx) {
                            const r = rules[ctx.dataIndex];
                            return ` Confidence: ${ctx.parsed.x.toFixed(1)}% | Lift: ${r.lift} | Support: ${r.support_pct}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    min: 0,
                    max: 100,
                    ticks: { callback: val => `${val}%` },
                    grid: { color: '#F1F5F9' }
                },
                y: {
                    grid: { display: false }
                }
            }
        }
    });
}

function renderRulesTable(rules) {
    const tbody = document.getElementById('assocRulesTbody');
    tbody.innerHTML = '';

    if (rules.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 24px;">No association rules found for the selected thresholds.</td></tr>`;
        return;
    }

    rules.forEach(r => {
        const tr = document.createElement('tr');
        
        let takeaway = "Moderate category persistence";
        if (r.lift > 3.0) {
            takeaway = "Extremely strong retention / correlation (Lift > 4)";
        } else if (r.lift > 2.0) {
            takeaway = "Strong retention / correlation (Lift > 2)";
        }

        tr.innerHTML = `
            <td><code style="color: var(--accent-blue); font-weight: 700; background: #EFF6FF; padding: 2px 6px; border-radius: 4px;">${r.antecedent}</code></td>
            <td><code style="color: var(--accent-teal); font-weight: 700; background: #F0FDFA; padding: 2px 6px; border-radius: 4px;">${r.consequent}</code></td>
            <td><strong>${(r.support * 100).toFixed(1)}%</strong> <span style="color: var(--text-muted); font-size: 11px;">(${r.support})</span></td>
            <td><strong>${(r.confidence * 100).toFixed(1)}%</strong> <span style="color: var(--text-muted); font-size: 11px;">(${r.confidence})</span></td>
            <td><span class="badge badge-high" style="font-size: 12px;">${r.lift.toFixed(2)}x</span></td>
            <td><span style="font-size: 12px; color: var(--text-secondary);">${takeaway}</span></td>
        `;
        tbody.appendChild(tr);
    });
}
