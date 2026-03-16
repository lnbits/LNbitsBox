(function () {
    const D = window.LNbitsBoxDashboard;
    D.state.wifiSelectedSsid = '';
    D.state.wifiSelectedFlags = '';
    D.timers.wifiConnectPoll = null;

    D.clearWifiScanList = function () {
        const container = D.el('wifi-scan-list');
        if (container) {
            container.replaceChildren();
        }
        return container;
    };

    D.renderWifiScanMessage = function (message, className) {
        const container = D.clearWifiScanList();
        if (!container) return;
        const text = document.createElement('p');
        text.className = className;
        text.textContent = message;
        container.appendChild(text);
    };

    D.renderWifiScanLoading = function () {
        const container = D.clearWifiScanList();
        if (!container) return;

        const wrapper = document.createElement('div');
        wrapper.className = 'flex items-center justify-center py-8';

        const spinner = document.createElement('div');
        spinner.className = 'w-5 h-5 border-2 border-ln-pink border-t-transparent rounded-full animate-spin mr-3';

        const label = document.createElement('span');
        label.className = 'text-ln-muted font-mono text-sm';
        label.textContent = 'Scanning...';

        wrapper.appendChild(spinner);
        wrapper.appendChild(label);
        container.appendChild(wrapper);
    };

    D.renderWifiScanResults = function (networks) {
        const container = D.clearWifiScanList();
        if (!container) return;

        const list = document.createElement('div');
        list.className = 'space-y-1 max-h-72 overflow-y-auto';

        networks.forEach(function (net) {
            const button = document.createElement('button');
            button.type = 'button';
            button.dataset.wifiSsid = net.ssid || '';
            button.dataset.wifiFlags = net.flags || '';
            button.className = 'wifi-network-btn w-full flex items-center justify-between px-3 py-2.5 rounded-lg hover:bg-ln-surface transition-colors group';

            const left = document.createElement('div');
            left.className = 'flex items-center gap-2 min-w-0';

            if (D.isEncrypted(net.flags)) {
                const lock = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                lock.setAttribute('class', 'w-3.5 h-3.5 text-ln-muted shrink-0');
                lock.setAttribute('fill', 'currentColor');
                lock.setAttribute('viewBox', '0 0 20 20');
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('fill-rule', 'evenodd');
                path.setAttribute('clip-rule', 'evenodd');
                path.setAttribute('d', 'M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z');
                lock.appendChild(path);
                left.appendChild(lock);
            }

            const ssid = document.createElement('span');
            ssid.className = 'font-mono text-sm truncate';
            ssid.textContent = net.ssid || '';
            left.appendChild(ssid);

            const signal = document.createElement('span');
            signal.className = 'font-mono text-sm text-ln-muted shrink-0 ml-2';
            signal.textContent = D.signalBars(net.signal);

            button.appendChild(left);
            button.appendChild(signal);
            list.appendChild(button);
        });

        container.appendChild(list);
    };

    D.signalBars = function (dbm) {
        if (dbm >= -50) return '\u2582\u2584\u2586\u2588';
        if (dbm >= -60) return '\u2582\u2584\u2586\u2007';
        if (dbm >= -70) return '\u2582\u2584\u2007\u2007';
        return '\u2582\u2007\u2007\u2007';
    };

    D.isEncrypted = function (flags) {
        return !!(flags && (flags.includes('WPA') || flags.includes('WEP')));
    };

    D.showWifiView = function (id) {
        ['wifi-scan-list', 'wifi-connect-form', 'wifi-connecting', 'wifi-result'].forEach(function (viewId) {
            D.el(viewId).classList.toggle('hidden', viewId !== id);
        });
    };

    D.openWifiScan = async function () {
        D.el('wifi-modal').classList.remove('hidden');
        D.showWifiView('wifi-scan-list');
        D.renderWifiScanLoading();
        try {
            const resp = await fetch('/box/api/wifi/scan', { method: 'POST' });
            if (!resp.ok) throw new Error('Scan failed');
            const data = await resp.json();
            if (data.error) throw new Error(data.error);
            if (!data.networks || data.networks.length === 0) {
                D.renderWifiScanMessage('No networks found', 'text-ln-muted font-mono text-sm text-center py-8');
                return;
            }
            D.renderWifiScanResults(data.networks);
        } catch (error) {
            const message = error && error.message ? error.message : 'Scan failed';
            D.renderWifiScanMessage('Scan failed: ' + message, 'text-red-400 font-mono text-sm text-center py-8');
        }
    };

    D.selectWifiNetwork = function (ssid, flags) {
        D.state.wifiSelectedSsid = ssid;
        D.state.wifiSelectedFlags = flags;
        D.el('wifi-connect-ssid').textContent = ssid;
        D.el('wifi-password').value = '';
        D.el('wifi-password-group').classList.toggle('hidden', !D.isEncrypted(flags));
        D.showWifiView('wifi-connect-form');
    };

    D.showScanList = function () {
        D.showWifiView('wifi-scan-list');
    };

    D.connectToWifi = async function () {
        const password = D.el('wifi-password').value;
        D.showWifiView('wifi-connecting');
        D.el('wifi-connecting-text').textContent = 'Connecting to ' + D.state.wifiSelectedSsid + '...';
        try {
            const resp = await fetch('/box/api/wifi/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ssid: D.state.wifiSelectedSsid, password: password }),
            });
            const data = await resp.json();
            if (data.status === 'error') {
                D.showWifiResult(false, data.message, '');
                return;
            }
        } catch (error) {
            D.showWifiResult(false, 'Failed to start connection', '');
            return;
        }
        D.timers.wifiConnectPoll = setInterval(async function () {
            try {
                const resp = await fetch('/box/api/wifi/connect/status');
                const data = await resp.json();
                if (data.status === 'success') {
                    clearInterval(D.timers.wifiConnectPoll);
                    D.timers.wifiConnectPoll = null;
                    D.showWifiResult(true, data.message, data.ip);
                    setTimeout(D.fetchStats, 2000);
                } else if (data.status === 'failed') {
                    clearInterval(D.timers.wifiConnectPoll);
                    D.timers.wifiConnectPoll = null;
                    D.showWifiResult(false, data.message, '');
                }
            } catch (error) {}
        }, 2000);
    };

    D.showWifiResult = function (success, message, ip) {
        D.showWifiView('wifi-result');
        const icon = D.el('wifi-result-icon');
        const text = D.el('wifi-result-text');
        const ipEl = D.el('wifi-result-ip');
        if (success) {
            icon.className = 'w-8 h-8 rounded-full mb-3 bg-emerald-400';
            text.textContent = message;
            text.className = 'font-mono text-sm mb-1 text-emerald-400';
            ipEl.textContent = ip ? 'IP: ' + ip : '';
            setTimeout(function () {
                if (!D.el('wifi-modal').classList.contains('hidden')) {
                    D.closeWifiModal();
                }
            }, 3000);
        } else {
            icon.className = 'w-8 h-8 rounded-full mb-3 bg-red-400';
            text.textContent = message;
            text.className = 'font-mono text-sm mb-1 text-red-400';
            ipEl.textContent = '';
        }
    };

    D.closeWifiModal = function () {
        D.el('wifi-modal').classList.add('hidden');
        if (D.timers.wifiConnectPoll) {
            clearInterval(D.timers.wifiConnectPoll);
            D.timers.wifiConnectPoll = null;
        }
    };
})();
