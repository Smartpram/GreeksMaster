let currentPage = 1;

function buildQuery() {
    const inst = document.getElementById('filterInstrument').value.trim();
    const gid = document.getElementById('filterGttId').value.trim();
    const status = document.getElementById('filterStatus').value;
    const perPage = document.getElementById('perPage').value;
    const params = new URLSearchParams();
    if (inst) params.append('instrument', inst);
    if (gid) params.append('gtt_order_id', gid);
    if (status) params.append('status', status);
    params.append('page', currentPage);
    params.append('per_page', perPage);
    return params.toString();
}

async function fetchGTT() {
    try {
        const q = buildQuery();
        const res = await fetch(API_GTT_TABLE + (q ? ('?' + q) : ''));
        const payload = await res.json();
        if (!payload.success) {
            document.getElementById('gttBody').innerHTML = `<tr><td colspan="8">Error: ${payload.error}</td></tr>`;
            return;
        }
        const meta = payload.data || {};
        const rows = meta.items || [];
        const body = document.getElementById('gttBody');
        body.innerHTML = '';

        if (rows.length === 0) {
            body.innerHTML = '<tr><td colspan="8" class="text-muted">No GTT records</td></tr>';
            return;
        }

    for (const r of rows) {
            const legsHtml = r.legs.map(l => `
                <div class="leg-row">
                    <strong>${l.gtt_leg_type || ''}</strong> ${l.action || ''} @ ${l.trigger_price || ''} / ${l.limit_price || ''}
                    <span class="badge bg-secondary ms-2">${l.status || ''}</span>
                </div>`).join('');

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${r.order_datetime || ''}</td>
                <td>${r.gtt_order_id || ''}</td>
                <td>${r.fresh_order_id || ''}</td>
                <td>${r.instrument || ''}</td>
                <td>${r.quantity || ''}</td>
                <td>${r.gtt_type || ''}</td>
                <td>${r.status_summary || ''}</td>
                <td>${legsHtml}</td>
            `;
            body.appendChild(tr);
        }
        renderPagination(meta.total || 0, meta.page || 1, meta.per_page || 25);
        return meta;
    } catch (e) {
        document.getElementById('gttBody').innerHTML = `<tr><td colspan="8">Exception: ${e}</td></tr>`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    fetchGTT();
    document.getElementById('refreshBtn').addEventListener('click', () => { currentPage = 1; fetchGTT(); });
    document.getElementById('filterInstrument').addEventListener('change', () => { currentPage = 1; fetchGTT(); });
    document.getElementById('filterGttId').addEventListener('change', () => { currentPage = 1; fetchGTT(); });
    document.getElementById('filterStatus').addEventListener('change', () => { currentPage = 1; fetchGTT(); });
    document.getElementById('perPage').addEventListener('change', () => { currentPage = 1; fetchGTT(); });
});

function renderPagination(total, page, per_page) {
    const pages = Math.ceil(total / per_page) || 1;
    const container = document.getElementById('pagination');
    container.innerHTML = '';
    for (let i = 1; i <= pages; i++) {
        const li = document.createElement('li');
        li.className = 'page-item' + (i === page ? ' active' : '');
        const a = document.createElement('a');
        a.className = 'page-link';
        a.href = '#';
        a.textContent = i;
        a.addEventListener('click', (e) => { e.preventDefault(); currentPage = i; fetchGTT(); });
        li.appendChild(a);
        container.appendChild(li);
    }
}
