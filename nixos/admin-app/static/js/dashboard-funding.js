(function () {
    const D = window.LNbitsBoxDashboard;
    if (!D) return;

    function fmt(value) {
        if (value === null || value === undefined) return '--';
        const n = Number(value);
        return Number.isFinite(n) ? n.toLocaleString() : '--';
    }

    function renderChannels(channels) {
        const list = D.el('phoenixd-channels-list');
        if (!list) return;
        if (!Array.isArray(channels) || channels.length === 0) {
            list.innerHTML = '<div class="px-3 py-3 text-xs font-mono text-ln-muted">No channels reported.</div>';
            return;
        }
        list.innerHTML = channels.map(function (channel) {
            const state = channel.state || channel.status || 'unknown';
            const local = channel.toLocal || channel.toLocalMsat || channel.balanceMsat || null;
            const remote = channel.toRemote || channel.toRemoteMsat || null;
            const id = channel.channelId || channel.id || channel.txId || 'channel';
            return '<div class="px-3 py-3 grid grid-cols-1 md:grid-cols-4 gap-2 text-xs font-mono">' +
                '<div class="text-ln-text break-all md:col-span-2">' + D.escapeHtml(id) + '</div>' +
                '<div class="text-ln-muted">state: <span class="text-ln-text">' + D.escapeHtml(state) + '</span></div>' +
                '<div class="text-ln-muted">local: <span class="text-ln-text">' + fmt(local !== null ? Math.floor(Number(local) / 1000) : null) + '</span> sats</div>' +
                (remote !== null ? '<div class="text-ln-muted md:col-start-4">remote: <span class="text-ln-text">' + fmt(Math.floor(Number(remote) / 1000)) + '</span> sats</div>' : '') +
                '</div>';
        }).join('');
    }

    function sourceLabel(source) {
        return source === 'phoenixd' ? 'Phoenixd' : 'Spark';
    }

    function sourceSummary(source, switching) {
        const prefix = switching ? 'Switching to ' + sourceLabel(source) + '... ' : '';
        return prefix + (
            source === 'phoenixd'
                ? 'LNbits will use the local Phoenixd API on port 9740.'
                : 'LNbits will use the local Spark sidecar API on port 8765.'
        );
    }

    function showSelectedPanel(source, switching) {
        D.setText('funding-selected-label', switching ? 'Switching...' : sourceLabel(source));
        D.setText('funding-source-summary', sourceSummary(source, switching));
        D.setText('funding-spark-state', source === 'spark' ? (switching ? 'Switching...' : 'Selected') : 'Stopped');
        D.setText('funding-phoenixd-state', source === 'phoenixd' ? (switching ? 'Switching...' : 'Selected') : 'Stopped');
        document.querySelectorAll('[data-funding-panel]').forEach(function (panel) {
            panel.classList.toggle('hidden', panel.dataset.fundingPanel !== source);
        });
    }

    D.renderFundingSources = function (payload) {
        if (!payload || !payload.sources) return;
        const selected = payload.selected || 'spark';
        const selectedLabel = payload.sources[selected]?.label || selected;
        const select = D.el('funding-source-select');
        D.state.confirmedFundingSource = selected;
        D.setText('funding-selected-label', selectedLabel);
        D.setText(
            'funding-source-summary',
            selected === 'phoenixd'
                ? 'Phoenixd is selected. LNbits will use the local Phoenixd API on port 9740.'
                : 'Spark is selected. LNbits will use the local Spark sidecar API on port 8765.'
        );
        D.setText('funding-spark-state', selected === 'spark' ? 'Selected' : D.serviceStatusLabel(payload.sources.spark?.service_status));
        D.setText('funding-phoenixd-state', selected === 'phoenixd' ? 'Selected' : D.serviceStatusLabel(payload.sources.phoenixd?.service_status));
        if (select) {
            select.value = selected;
            select.dataset.confirmedValue = selected;
        }

        document.querySelectorAll('[data-funding-panel]').forEach(function (panel) {
            panel.classList.toggle('hidden', panel.dataset.fundingPanel !== selected);
        });

        const phoenixd = payload.phoenixd || {};
        const balance = phoenixd.balance || {};
        D.setText('phoenixd-balance', fmt(balance.balance));
        D.setText('phoenixd-fee-credit', fmt(balance.fee_credit));
        D.setText('phoenixd-channel-count', fmt(phoenixd.channel_count));
        renderChannels(phoenixd.channels || []);
    };

    D.fetchFundingSources = async function () {
        const resp = await fetch('/box/api/funding-sources');
        if (!resp.ok) return;
        const payload = await resp.json();
        D.renderFundingSources(payload.data || payload);
    };

    async function selectFundingSource(source, select) {
        const previous = D.state.confirmedFundingSource || select.dataset.confirmedValue || select.value || 'spark';
        if (source === previous) return;
        showSelectedPanel(source, true);
        select.disabled = true;
        select.classList.add('opacity-60', 'cursor-not-allowed');
        try {
            const resp = await fetch('/box/api/funding-sources/select', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source: source }),
            });
            const payload = await resp.json();
            if (payload.status !== 'ok') {
                D.showNotice(payload.message || 'Could not switch funding source.', 'Error');
                select.value = previous;
                showSelectedPanel(previous, false);
                return;
            }
            D.renderFundingSources(payload.data || payload);
            D.state.confirmedFundingSource = (payload.data || payload).selected || source;
            if (typeof D.fetchStats === 'function') setTimeout(D.fetchStats, 1200);
            D.showNotice(payload.message, 'Funding Source Updated');
        } catch (error) {
            select.value = previous;
            showSelectedPanel(previous, false);
            D.showNotice('Request failed', 'Error');
        } finally {
            select.disabled = false;
            select.classList.remove('opacity-60', 'cursor-not-allowed');
        }
    }

    const select = D.el('funding-source-select');
    if (select) {
        select.addEventListener('change', function () {
            selectFundingSource(select.value, select);
        });
    }

    const initial = D.el('initial-funding-sources');
    if (initial) {
        try {
            D.renderFundingSources(JSON.parse(initial.textContent || '{}'));
        } catch (error) {}
    }
})();
