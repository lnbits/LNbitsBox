(function () {
    const D = window.LNbitsBoxDashboard;

    D.formatBytes = function (bytes) {
        if (bytes === 0) return '0 B';
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + units[i];
    };

    D.tempColor = function (temp) {
        if (temp === null) return 'text-ln-muted';
        if (temp < 55) return 'text-emerald-400';
        if (temp < 70) return 'text-amber-400';
        return 'text-red-400';
    };

    D.svcColor = function (status) {
        return status === 'active' ? 'bg-emerald-400' : 'bg-red-400';
    };

    D.serviceStatusLabel = function (status) {
        const s = status || 'unknown';
        if (s === 'active') return 'Running';
        if (s === 'inactive') return 'Stopped';
        if (s === 'activating') return 'Starting';
        if (s === 'deactivating') return 'Stopping';
        if (s === 'failed') return 'Error';
        return s;
    };

    D.setServiceActionVisibility = function (service, status, options) {
        options = options || {};
        const loading = D.el('svc-' + service + '-actions-loading');
        const createBtn = D.el('svc-' + service + '-create-btn');
        const restartBtn = D.el('svc-' + service + '-restart-btn');
        const startBtn = D.el('svc-' + service + '-start-btn');
        const stopBtn = D.el('svc-' + service + '-stop-btn');
        if (!startBtn || !stopBtn || !restartBtn) return;
        if (loading) loading.classList.add('hidden');
        if (createBtn) createBtn.classList.add('hidden');
        if (service === 'tunnel' && options.hasTunnel === false) {
            restartBtn.classList.add('hidden');
            startBtn.classList.add('hidden');
            stopBtn.classList.add('hidden');
            if (createBtn) createBtn.classList.remove('hidden');
            return;
        }
        const isActive = status === 'active';
        restartBtn.classList.toggle('hidden', !isActive);
        startBtn.classList.toggle('hidden', isActive);
        stopBtn.classList.toggle('hidden', !isActive);
    };

    D.fetchStats = async function () {
        try {
            const resp = await fetch('/box/api/stats');
            if (!resp.ok) return;
            const payload = await resp.json();
            const s = payload.current;

            const balance = s.spark_balance;
            D.setText('stat-balance', balance && balance.balance !== undefined ? Number(balance.balance).toLocaleString() : '--');
            D.setText('stat-uptime', s.uptime.formatted);

            const tempEl = D.el('stat-temp');
            if (tempEl) {
                tempEl.textContent = s.cpu_temp !== null ? s.cpu_temp : '--';
                tempEl.className = 'text-2xl sm:text-3xl font-display font-bold ' + D.tempColor(s.cpu_temp);
            }

            D.setText('stat-disk', s.disk.percent + '%');
            const diskBar = D.el('stat-disk-bar');
            if (diskBar) diskBar.style.width = s.disk.percent + '%';
            D.setText('stat-disk-detail', D.formatBytes(s.disk.used) + ' / ' + D.formatBytes(s.disk.total));

            D.setText('stat-ram', s.ram.percent + '%');
            const ramBar = D.el('stat-ram-bar');
            if (ramBar) ramBar.style.width = s.ram.percent + '%';
            D.setText('stat-ram-detail', D.formatBytes(s.ram.used) + ' / ' + D.formatBytes(s.ram.total));

            const onion = s.tor_onion;
            if (onion) {
                D.setText('stat-tor-address', onion);
                const torDot = D.el('tor-dot');
                if (torDot) torDot.className = 'w-2.5 h-2.5 rounded-full bg-purple-400';
                const torCopy = D.el('tor-copy-btn');
                if (torCopy) torCopy.classList.remove('hidden');
            } else {
                D.setText('stat-tor-address', 'Waiting for Tor...');
                const torDot = D.el('tor-dot');
                if (torDot) torDot.className = 'w-2.5 h-2.5 rounded-full bg-ln-muted animate-pulse';
                const torCopy = D.el('tor-copy-btn');
                if (torCopy) torCopy.classList.add('hidden');
            }

            ['lnbits', 'spark-sidecar', 'tor'].forEach(function (svc) {
                const status = s.services[svc] || 'unknown';
                const dot = D.el('svc-' + svc + '-dot');
                if (dot) dot.className = 'w-2.5 h-2.5 rounded-full ' + D.svcColor(status);
                D.setText('svc-' + svc + '-status', D.serviceStatusLabel(status));
                D.setServiceActionVisibility(svc, status);
            });

            if (s.network) {
                const net = s.network;
                const internetDot = D.el('net-internet-dot');
                if (internetDot) internetDot.className = 'w-2.5 h-2.5 rounded-full ' + (net.internet ? 'bg-emerald-400' : 'bg-red-400');
                D.setText('net-internet-status', net.internet ? 'Connected' : 'Disconnected');
                if (net.wifi) {
                    const wifiDot = D.el('net-wifi-dot');
                    if (wifiDot) wifiDot.className = 'w-2.5 h-2.5 rounded-full bg-emerald-400 shrink-0';
                    D.setText('net-wifi-status', '"' + net.wifi.ssid + '" (' + net.wifi.ip + ')');
                } else {
                    const wifiDot = D.el('net-wifi-dot');
                    if (wifiDot) wifiDot.className = 'w-2.5 h-2.5 rounded-full bg-gray-600 shrink-0';
                    D.setText('net-wifi-status', 'Not connected');
                }
                if (net.ethernet) {
                    const ethDot = D.el('net-eth-dot');
                    if (ethDot) ethDot.className = 'w-2.5 h-2.5 rounded-full bg-emerald-400';
                    D.setText('net-eth-status', net.ethernet.ip);
                } else {
                    const ethDot = D.el('net-eth-dot');
                    if (ethDot) ethDot.className = 'w-2.5 h-2.5 rounded-full bg-gray-600';
                    D.setText('net-eth-status', 'Not connected');
                }
            }

            if (D.charts.cpu && D.charts.ram && D.charts.temp) {
                const labels = payload.history.timestamps.map(function (timestamp) {
                    const date = new Date(timestamp);
                    return date.getHours().toString().padStart(2, '0') + ':' + date.getMinutes().toString().padStart(2, '0');
                });
                D.charts.cpu.data.labels = labels;
                D.charts.cpu.data.datasets[0].data = payload.history.cpu;
                D.charts.cpu.update('none');
                D.charts.ram.data.labels = labels;
                D.charts.ram.data.datasets[0].data = payload.history.ram;
                D.charts.ram.update('none');
                D.charts.temp.data.labels = labels;
                D.charts.temp.data.datasets[0].data = payload.history.temp;
                D.charts.temp.update('none');
            }
        } catch (error) {
            console.error('Stats fetch failed:', error);
        }
    };

    (function seedMockData() {
        if (!D.root || D.root.dataset.devMode !== 'true') return;
        const now = Date.now();
        const points = 60;
        const labels = [];
        const cpu = [];
        const ram = [];
        const temp = [];
        for (let i = points; i > 0; i -= 1) {
            const t = new Date(now - i * 30000);
            labels.push(t.getHours().toString().padStart(2, '0') + ':' + t.getMinutes().toString().padStart(2, '0'));
            cpu.push(Math.round(15 + 40 * Math.sin(i / 8) ** 2 + Math.random() * 10));
            ram.push(Math.round(45 + 15 * Math.sin(i / 12) + Math.random() * 5));
            temp.push(Math.round(42 + 12 * Math.sin(i / 10) + Math.random() * 3));
        }
        if (!D.charts.cpu || !D.charts.ram || !D.charts.temp) return;
        D.charts.cpu.data.labels = labels;
        D.charts.cpu.data.datasets[0].data = cpu;
        D.charts.cpu.update('none');
        D.charts.ram.data.labels = labels;
        D.charts.ram.data.datasets[0].data = ram;
        D.charts.ram.update('none');
        D.charts.temp.data.labels = labels;
        D.charts.temp.data.datasets[0].data = temp;
        D.charts.temp.update('none');
    })();

    D.updateLnbitsStatus = async function () {
        const statusDot = D.el('lnbits-status-dot');
        const statusText = D.el('lnbits-status-text');
        const statusBadge = D.el('lnbits-status-badge');
        const statusCard = D.el('lnbits-status-card');
        const openLink = D.el('lnbits-open-link');
        if (!statusDot || !statusText || !statusBadge || !statusCard || !openLink) return;
        try {
            const resp = await fetch('/box/api/lnbits-status');
            if (!resp.ok) return;
            const data = await resp.json();
            if (data.status === 'running') {
                statusDot.className = 'w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse transition-colors duration-300';
                statusText.textContent = 'LNbits is running';
                statusText.className = 'text-emerald-400/70 text-sm transition-colors duration-300';
                statusBadge.textContent = 'running';
                statusBadge.className = 'text-xs font-mono uppercase tracking-wider px-2 py-0.5 rounded-full border transition-all duration-300 text-emerald-400 border-emerald-400/30 bg-emerald-400/5';
                statusCard.className = 'bg-ln-surface border border-emerald-400/20 rounded-xl p-4 mb-6 transition-all duration-500';
                openLink.classList.remove('opacity-50', 'pointer-events-none');
            } else if (data.status === 'starting') {
                statusDot.className = 'w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse transition-colors duration-300';
                statusText.textContent = 'LNbits is starting...';
                statusText.className = 'text-amber-400/70 text-sm transition-colors duration-300';
                statusBadge.textContent = 'starting';
                statusBadge.className = 'text-xs font-mono uppercase tracking-wider px-2 py-0.5 rounded-full border transition-all duration-300 text-amber-400 border-amber-400/30 bg-amber-400/5';
                statusCard.className = 'bg-ln-surface border border-amber-400/20 rounded-xl p-4 mb-6 transition-all duration-500';
                openLink.classList.add('opacity-50', 'pointer-events-none');
            } else {
                statusDot.className = 'w-2.5 h-2.5 rounded-full bg-red-400 transition-colors duration-300';
                statusText.textContent = data.status === 'error' ? 'LNbits error (HTTP ' + data.code + ')' : 'LNbits is stopped';
                statusText.className = 'text-red-400/70 text-sm transition-colors duration-300';
                statusBadge.textContent = data.status;
                statusBadge.className = 'text-xs font-mono uppercase tracking-wider px-2 py-0.5 rounded-full border transition-all duration-300 text-red-400 border-red-400/30 bg-red-400/5';
                statusCard.className = 'bg-ln-surface border border-red-400/20 rounded-xl p-4 mb-6 transition-all duration-500';
                openLink.classList.add('opacity-50', 'pointer-events-none');
            }
        } catch (error) {
            console.error('LNbits status check failed:', error);
        }
    };

    D.config.lnbitsPollMs = 15000;
    D.config.hiddenTabPollMs = 60000;

    D.nextLnbitsPollDelay = function () {
        return document.hidden ? D.config.hiddenTabPollMs : D.config.lnbitsPollMs;
    };

    D.runLnbitsPollLoop = async function () {
        await D.updateLnbitsStatus();
        D.timers.lnbitsPollLoop = setTimeout(D.runLnbitsPollLoop, D.nextLnbitsPollDelay());
    };

    D.restartLnbitsPollLoop = function () {
        clearTimeout(D.timers.lnbitsPollLoop);
        D.timers.lnbitsPollLoop = null;
        D.runLnbitsPollLoop();
    };

    D.copyOnion = async function () {
        const addrEl = D.el('stat-tor-address');
        if (!addrEl) return;
        const addr = addrEl.textContent;
        if (!addr || addr === '--' || addr.startsWith('Waiting')) return;
        try {
            await navigator.clipboard.writeText('http://' + addr);
        } catch (error) {
            const textarea = document.createElement('textarea');
            textarea.value = 'http://' + addr;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
        }
        const btn = D.el('tor-copy-btn');
        if (btn) {
            btn.textContent = 'Copied!';
            setTimeout(function () { btn.textContent = 'Copy'; }, 1500);
        }
    };

    D.fetchStats();
    setInterval(D.fetchStats, 10000);
    D.restartLnbitsPollLoop();
    document.addEventListener('visibilitychange', D.restartLnbitsPollLoop);
})();
