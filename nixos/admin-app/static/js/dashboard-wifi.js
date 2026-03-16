(function () {
    const D = window.LNbitsBoxDashboard;
    D.state.wifiSelectedSsid = '';
    D.state.wifiSelectedFlags = '';
    D.state.wifiSudoPassword = '';
    D.timers.wifiConnectPoll = null;

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

    D.openWifiScan = async function (sudoPassword) {
        if (!sudoPassword && !D.state.wifiSudoPassword) {
            D.requestSudoPassword('Scan Wi-Fi Networks', 'Enter your admin password to scan for Wi-Fi networks.', 'Scan', D.openWifiScan);
            return;
        }
        D.state.wifiSudoPassword = sudoPassword || D.state.wifiSudoPassword;
        D.el('wifi-modal').classList.remove('hidden');
        D.showWifiView('wifi-scan-list');
        D.el('wifi-scan-list').innerHTML = '<div class="flex items-center justify-center py-8"><div class="w-5 h-5 border-2 border-ln-pink border-t-transparent rounded-full animate-spin mr-3"></div><span class="text-ln-muted font-mono text-sm">Scanning...</span></div>';
        try {
            const resp = await fetch('/box/api/wifi/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sudo_password: D.state.wifiSudoPassword }),
            });
            const data = await resp.json();
            if (data.code === 'sudo_required') {
                D.state.wifiSudoPassword = '';
                D.requestSudoPassword('Scan Wi-Fi Networks', data.message || 'Enter your admin password to scan for Wi-Fi networks.', 'Scan', D.openWifiScan);
                return;
            }
            if (!resp.ok) throw new Error('Scan failed');
            if (data.error) throw new Error(data.error);
            if (!data.networks || data.networks.length === 0) {
                D.el('wifi-scan-list').innerHTML = '<p class="text-ln-muted font-mono text-sm text-center py-8">No networks found</p>';
                return;
            }
            let html = '<div class="space-y-1 max-h-72 overflow-y-auto">';
            data.networks.forEach(function (net) {
                const lock = D.isEncrypted(net.flags) ? '<svg class="w-3.5 h-3.5 text-ln-muted shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"></path></svg>' : '';
                html += '<button type="button" data-wifi-ssid="' + encodeURIComponent(net.ssid) + '" data-wifi-flags="' + encodeURIComponent(net.flags || '') + '" class="wifi-network-btn w-full flex items-center justify-between px-3 py-2.5 rounded-lg hover:bg-ln-surface transition-colors group">' +
                    '<div class="flex items-center gap-2 min-w-0">' + lock + '<span class="font-mono text-sm truncate">' + net.ssid + '</span></div>' +
                    '<span class="font-mono text-sm text-ln-muted shrink-0 ml-2">' + D.signalBars(net.signal) + '</span></button>';
            });
            html += '</div>';
            D.el('wifi-scan-list').innerHTML = html;
        } catch (error) {
            D.el('wifi-scan-list').innerHTML = '<p class="text-red-400 font-mono text-sm text-center py-8">Scan failed: ' + error.message + '</p>';
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

    D.connectToWifi = async function (sudoPassword) {
        const password = D.el('wifi-password').value;
        if (!sudoPassword && !D.state.wifiSudoPassword) {
            D.requestSudoPassword('Connect to Wi-Fi', 'Enter your admin password to update Wi-Fi settings.', 'Connect', D.connectToWifi);
            return;
        }
        D.state.wifiSudoPassword = sudoPassword || D.state.wifiSudoPassword;
        D.showWifiView('wifi-connecting');
        D.el('wifi-connecting-text').textContent = 'Connecting to ' + D.state.wifiSelectedSsid + '...';
        try {
            const resp = await fetch('/box/api/wifi/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ssid: D.state.wifiSelectedSsid, password: password, sudo_password: D.state.wifiSudoPassword }),
            });
            const data = await resp.json();
            if (data.code === 'sudo_required') {
                D.state.wifiSudoPassword = '';
                D.showWifiView('wifi-connect-form');
                D.requestSudoPassword('Connect to Wi-Fi', data.message || 'Enter your admin password to update Wi-Fi settings.', 'Connect', D.connectToWifi);
                return;
            }
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
        D.state.wifiSudoPassword = '';
        if (D.timers.wifiConnectPoll) {
            clearInterval(D.timers.wifiConnectPoll);
            D.timers.wifiConnectPoll = null;
        }
    };
})();
