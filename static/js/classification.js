/**
 * Classification Module Client Scripts
 * Handles Decision Tree live execution, confusion matrix rendering, and test records table
 */

document.addEventListener('DOMContentLoaded', () => {
    loadClassificationResults();

    const btnRun = document.getElementById('btnRunClf');
    if (btnRun) {
        btnRun.addEventListener('click', runClassification);
    }
});

async function loadClassificationResults() {
    try {
        const res = await fetch('/api/classification/results');
        const data = await res.json();
        renderClassificationUI(data);
    } catch (err) {
        console.error("Error loading classification results:", err);
    }
}

async function runClassification() {
    const btn = document.getElementById('btnRunClf');
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Running...`;

    const payload = {
        max_depth: parseInt(document.getElementById('clfMaxDepth').value),
        test_size: parseFloat(document.getElementById('clfTestSize').value),
        random_state: parseInt(document.getElementById('clfRandomState').value)
    };

    try {
        const res = await fetch('/api/classification/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        renderClassificationUI(data);
    } catch (err) {
        alert("Classification failed: " + err);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-play"></i> Run Classification`;
    }
}

function renderClassificationUI(data) {
    document.getElementById('clfModelName').textContent = data.model_name;
    document.getElementById('clfValidCount').textContent = data.valid_records_count;
    document.getElementById('clfSplit').textContent = `${data.train_count} / ${data.test_count}`;
    document.getElementById('clfAccuracy').textContent = `${data.accuracy}%`;
    document.getElementById('clfRatio').textContent = `${data.accuracy_ratio} test records correctly classified`;

    if (data.tree_rules) {
        document.getElementById('clfTreeRules').textContent = data.tree_rules;
    }

    // Render Confusion Matrix Table
    const cm = data.confusion_matrix.matrix;
    const labels = data.confusion_matrix.labels;
    const cmContainer = document.getElementById('confusionMatrixContainer');

    let cmHtml = `
        <table style="width: 100%; border-collapse: collapse; text-align: center; font-size: 12px;">
            <thead>
                <tr>
                    <th style="padding: 6px; font-size: 11px; color: var(--text-muted); border-bottom: 1px solid var(--border-color);">Actual \\ Pred</th>
                    ${labels.map(l => `<th style="padding: 6px; font-size: 11px; color: var(--text-navy); border-bottom: 1px solid var(--border-color);">${l.replace(' Tourism', '')}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
    `;

    for (let r = 0; r < cm.length; r++) {
        cmHtml += `<tr><td style="padding: 8px 6px; font-weight: 600; color: var(--text-secondary); text-align: left; border-right: 1px solid var(--border-color);">${labels[r].replace(' Tourism', '')}</td>`;
        for (let c = 0; c < cm[r].length; c++) {
            const count = cm[r][c];
            const isDiagonal = (r === c);
            const bg = isDiagonal && count > 0 ? '#DCFCE7' : (count > 0 ? '#FEE2E2' : '#F8FAFC');
            const color = isDiagonal && count > 0 ? '#15803D' : (count > 0 ? '#B91C1C' : '#94A3B8');
            cmHtml += `<td style="padding: 8px; background-color: ${bg}; color: ${color}; font-weight: 700; border: 1px solid #E2E8F0;">${count}</td>`;
        }
        cmHtml += `</tr>`;
    }
    cmHtml += `</tbody></table>`;
    cmContainer.innerHTML = cmHtml;

    // Render Test Results Table
    const tbody = document.getElementById('clfTestResultsTbody');
    tbody.innerHTML = '';

    data.test_results.forEach(row => {
        const tr = document.createElement('tr');
        const outcomeBadge = row.is_correct 
            ? `<span class="badge badge-high"><i class="fa-solid fa-check" style="margin-right: 4px;"></i> Correct</span>`
            : `<span class="badge" style="background-color: #FEE2E2; color: #B91C1C;"><i class="fa-solid fa-xmark" style="margin-right: 4px;"></i> Misclassified</span>`;

        tr.innerHTML = `
            <td><strong style="color: var(--text-navy);">${row.country}</strong></td>
            <td>${row.arrivals_2022.toFixed(2)} M</td>
            <td>${row.arrivals_2023.toFixed(2)} M</td>
            <td><span class="badge badge-medium">${row.actual_category}</span></td>
            <td><span class="badge badge-medium">${row.predicted_category}</span></td>
            <td>${outcomeBadge}</td>
        `;
        tbody.appendChild(tr);
    });
}
