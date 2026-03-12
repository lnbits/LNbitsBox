(function () {
    const D = window.LNbitsBoxDashboard = window.LNbitsBoxDashboard || { state: {}, timers: {}, config: {} };

    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (csrfToken && !D.fetchWrapped) {
        const originalFetch = window.fetch;
        window.fetch = function (url, opts) {
            opts = opts || {};
            const method = (opts.method || 'GET').toUpperCase();
            if (method !== 'GET' && method !== 'HEAD') {
                opts.headers = Object.assign({}, opts.headers, { 'X-CSRFToken': csrfToken });
            }
            return originalFetch.call(this, url, opts);
        };
        D.fetchWrapped = true;
    }

    D.root = document.getElementById('dashboard-root');
    D.el = function (id) { return document.getElementById(id); };
    D.setText = function (id, value) {
        const el = D.el(id);
        if (el) el.textContent = value;
        return el;
    };
    D.setHtml = function (id, value) {
        const el = D.el(id);
        if (el) el.innerHTML = value;
        return el;
    };
    D.getCssVar = function (name) {
        return getComputedStyle(document.documentElement).getPropertyValue(name).trim().split(' ').join(',');
    };
    D.theme = {
        border: D.getCssVar('--ln-border'),
        muted: D.getCssVar('--ln-muted'),
    };

    D.showNotice = function (message, title) {
        D.setText('notice-title', title || 'Notice');
        D.setText('notice-message', message || '');
        const modal = D.el('notice-modal');
        if (modal) modal.classList.remove('hidden');
    };

    D.closeNoticeModal = function () {
        const modal = D.el('notice-modal');
        if (modal) modal.classList.add('hidden');
    };

    D.closeModal = function () {
        D.state.pendingAction = null;
        D.state.pendingActionButtonId = null;
        const modal = D.el('confirm-modal');
        if (modal) modal.classList.add('hidden');
    };

    D.setActionBusy = function (action, sourceButtonId) {
        const actionVerb = action.startsWith('start/') ? 'start'
            : action.startsWith('stop/') ? 'stop'
                : action.startsWith('restart/') ? 'restart'
                    : action === 'tunnel/stop' ? 'stop'
                        : action === 'tunnel/start' && sourceButtonId === 'svc-tunnel-restart-btn' ? 'restart'
                            : action === 'tunnel/start' ? 'start'
                                : null;
        const service = action.startsWith('start/') || action.startsWith('stop/') || action.startsWith('restart/')
            ? action.split('/')[1]
            : action.startsWith('tunnel/') ? 'tunnel' : null;
        if (!service || !actionVerb) return function () {};

        const ids = [
            'svc-' + service + '-start-btn',
            'svc-' + service + '-stop-btn',
            'svc-' + service + '-restart-btn',
        ];
        const labels = { start: 'Starting...', stop: 'Stopping...', restart: 'Restarting...' };
        const spinner = '<span class="inline-flex items-center gap-2"><span class="w-3.5 h-3.5 border-2 border-white/70 border-t-transparent rounded-full animate-spin"></span><span>' + labels[actionVerb] + '</span></span>';
        const buttons = ids.map(function (id) { return D.el(id); }).filter(Boolean);
        const target = D.el(sourceButtonId || ('svc-' + service + '-' + actionVerb + '-btn'));

        buttons.forEach(function (button) {
            button.dataset.prevDisabled = button.disabled ? '1' : '0';
            button.disabled = true;
            button.classList.add('opacity-60', 'cursor-not-allowed');
        });
        if (target) {
            target.dataset.prevHtml = target.innerHTML;
            target.innerHTML = spinner;
        }

        return function () {
            buttons.forEach(function (button) {
                button.disabled = button.dataset.prevDisabled === '1';
                button.classList.remove('opacity-60', 'cursor-not-allowed');
                delete button.dataset.prevDisabled;
            });
            if (target && target.dataset.prevHtml) {
                target.innerHTML = target.dataset.prevHtml;
                delete target.dataset.prevHtml;
            }
        };
    };

    D.confirmAction = function (action, message, buttonId) {
        D.state.pendingAction = action;
        D.state.pendingActionButtonId = buttonId || null;
        D.setText('confirm-title', 'Are you sure?');
        D.setText('confirm-message', message);
        const modal = D.el('confirm-modal');
        if (modal) modal.classList.remove('hidden');
        const btn = D.el('confirm-btn');
        if (!btn) return;
        btn.onclick = function () {
            D.executeAction(action, D.state.pendingActionButtonId);
        };
    };

    D.executeAction = async function (action, sourceButtonId) {
        D.closeModal();
        const releaseBusy = D.setActionBusy(action, sourceButtonId);
        try {
            const resp = await fetch('/box/api/' + action, { method: 'POST' });
            const data = await resp.json();
            if (data.status === 'ok') {
                if (typeof D.fetchStats === 'function') {
                    setTimeout(D.fetchStats, 1200);
                }
                if (action.startsWith('tunnel/') && typeof D.fetchTunnelStatus === 'function') {
                    setTimeout(D.fetchTunnelStatus, 1200);
                }
                const message = action === 'shutdown' ? 'LNbits Box is shutting down. Please wait 15 seconds before disconnecting the power supply.'
                    : action === 'reboot' ? 'Rebooting...'
                        : data.message;
                D.showNotice(message, 'Success');
            } else {
                D.showNotice('Error: ' + data.message, 'Error');
            }
        } catch (error) {
            D.showNotice('Request failed', 'Error');
        } finally {
            releaseBusy();
        }
    };

    const chartOpts = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 300 },
        plugins: {
            legend: { display: false },
            tooltip: {
                enabled: true,
                backgroundColor: 'rgb(' + D.getCssVar('--ln-card') + ')',
                titleColor: 'rgb(' + D.theme.muted + ')',
                bodyColor: 'rgb(' + D.getCssVar('--ln-text') + ')',
                borderColor: 'rgb(' + D.theme.border + ')',
                borderWidth: 1,
                titleFont: { family: 'JetBrains Mono', size: 11 },
                bodyFont: { family: 'JetBrains Mono', size: 12 },
                padding: 8,
                displayColors: false,
                callbacks: {
                    label: function (ctx) { return ctx.parsed.y.toFixed(1) + '%'; },
                },
            },
        },
        interaction: { mode: 'index', intersect: false },
        scales: {
            x: {
                display: true,
                grid: { display: false },
                ticks: {
                    color: 'rgb(' + D.theme.muted + ')',
                    font: { family: 'JetBrains Mono', size: 9 },
                    maxTicksLimit: 6,
                },
            },
            y: {
                min: 0,
                max: 100,
                grid: { color: 'rgba(' + D.theme.border + ',0.5)' },
                ticks: {
                    color: 'rgb(' + D.theme.muted + ')',
                    font: { family: 'JetBrains Mono', size: 10 },
                    callback: function (value) { return value + '%'; },
                },
            },
        },
        elements: {
            point: { radius: 0, hoverRadius: 5, hitRadius: 20, hoverBorderWidth: 2 },
            line: { tension: 0.3, borderWidth: 2 },
        },
    };

    D.charts = { cpu: null, ram: null, temp: null };

    const cpuCanvas = D.el('chart-cpu');
    const ramCanvas = D.el('chart-ram');
    const tempCanvas = D.el('chart-temp');
    if (typeof Chart !== 'undefined' && cpuCanvas && ramCanvas && tempCanvas) {
        D.charts.cpu = new Chart(cpuCanvas, {
            type: 'line',
            data: { labels: [], datasets: [{ data: [], borderColor: '#FF1EE6', backgroundColor: 'rgba(255,30,230,0.08)', fill: true }] },
            options: Object.assign({}, chartOpts),
        });
        D.charts.ram = new Chart(ramCanvas, {
            type: 'line',
            data: { labels: [], datasets: [{ data: [], borderColor: '#22d3ee', backgroundColor: 'rgba(34,211,238,0.08)', fill: true }] },
            options: Object.assign({}, chartOpts),
        });

        const tempChartOpts = JSON.parse(JSON.stringify(chartOpts));
        tempChartOpts.scales.y = {
            min: 20,
            max: 90,
            grid: { color: 'rgba(' + D.theme.border + ',0.5)' },
            ticks: {
                color: 'rgb(' + D.theme.muted + ')',
                font: { family: 'JetBrains Mono', size: 10 },
                callback: function (value) { return value + '°'; },
            },
        };
        tempChartOpts.plugins.tooltip.callbacks = { label: function (ctx) { return ctx.parsed.y.toFixed(1) + '°C'; } };
        D.charts.temp = new Chart(tempCanvas, {
            type: 'line',
            data: { labels: [], datasets: [{ data: [], borderColor: '#f59e0b', backgroundColor: 'rgba(245,158,11,0.08)', fill: true }] },
            options: tempChartOpts,
        });
    }
})();
