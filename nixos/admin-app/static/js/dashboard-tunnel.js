(function () {
    const D = window.LNbitsBoxDashboard;
    D.state.tunnel = null;
    D.timers.tunnelInvoicePoll = null;
    D.state.tunnelInvoiceQr = null;
    D.state.tunnelInvoiceLoading = false;
    D.config.tunnelExpiryAlertWindowMs = 24 * 60 * 60 * 1000;

    D.isTunnelAlertSupported = function () {
        return typeof window !== 'undefined' && 'Notification' in window;
    };

    D.formatExpiryCountdown = function (msLeft) {
        if (msLeft <= 0) return 'already expired';
        const hours = Math.ceil(msLeft / (60 * 60 * 1000));
        if (hours < 24) return 'in ' + hours + 'h';
        return 'in ' + Math.ceil(hours / 24) + 'd';
    };

    D.tunnelAlertStorageKey = function (tunnelId, expiresAt) {
        return 'lnbitsbox:tunnel-expiry-alert:' + (tunnelId || 'unknown') + ':' + (expiresAt || 'unknown');
    };

    D.tunnelAlertAlreadySent = function (key) {
        try {
            return !!localStorage.getItem(key);
        } catch (error) {
            return false;
        }
    };

    D.markTunnelAlertSent = function (key) {
        try {
            localStorage.setItem(key, new Date().toISOString());
        } catch (error) {}
    };

    D.updateTunnelAlertStatus = function (hasTunnel, expiresAt) {
        const statusEl = D.el('tunnel-alert-status');
        const buttonEl = D.el('tunnel-alert-enable-btn');
        if (!statusEl || !buttonEl) return;
        if (!D.isTunnelAlertSupported()) {
            statusEl.textContent = 'Browser notifications unsupported';
            buttonEl.disabled = true;
            buttonEl.classList.add('opacity-50');
            return;
        }
        const permission = Notification.permission;
        if (permission === 'granted') {
            if (!hasTunnel || !expiresAt) {
                statusEl.textContent = 'Alerts enabled';
            } else {
                const msLeft = new Date(expiresAt).getTime() - Date.now();
                statusEl.textContent = msLeft <= D.config.tunnelExpiryAlertWindowMs ? 'Expiry warning active (' + D.formatExpiryCountdown(msLeft) + ')' : 'Alerts enabled';
            }
            buttonEl.classList.add('hidden');
            return;
        }
        if (permission === 'denied') {
            statusEl.textContent = 'Blocked in browser settings';
            buttonEl.classList.add('hidden');
            return;
        }
        statusEl.textContent = hasTunnel ? 'Browser notifications off' : 'No active tunnel';
        buttonEl.classList.remove('hidden');
        buttonEl.disabled = false;
        buttonEl.classList.remove('opacity-50');
    };

    D.enableTunnelExpiryAlerts = async function () {
        if (!D.isTunnelAlertSupported()) {
            D.showNotice('Browser notifications are not supported on this device.', 'Tunnel Alerts');
            return;
        }
        try {
            const result = await Notification.requestPermission();
            const current = D.state.tunnel && D.state.tunnel.current_tunnel ? D.state.tunnel.current_tunnel : null;
            D.updateTunnelAlertStatus(!!(current && current.tunnel_id), current ? current.expires_at : null);
            if (result === 'granted') {
                D.showNotice('Tunnel expiry alerts enabled for this browser.', 'Tunnel Alerts');
            } else if (result === 'denied') {
                D.showNotice('Notifications are blocked. Enable them in browser settings.', 'Tunnel Alerts');
            }
        } catch (error) {
            D.showNotice('Failed to enable notifications.', 'Tunnel Alerts');
        }
    };

    D.maybeNotifyTunnelExpiry = function (currentTunnel) {
        if (!D.isTunnelAlertSupported() || Notification.permission !== 'granted') return;
        if (!currentTunnel || !currentTunnel.tunnel_id || !currentTunnel.expires_at) return;
        const expiresMs = new Date(currentTunnel.expires_at).getTime();
        if (Number.isNaN(expiresMs)) return;
        const msLeft = expiresMs - Date.now();
        if (msLeft > D.config.tunnelExpiryAlertWindowMs) return;
        const key = D.tunnelAlertStorageKey(currentTunnel.tunnel_id, currentTunnel.expires_at);
        if (D.tunnelAlertAlreadySent(key)) return;
        try {
            const notification = new Notification('Tunnel expires soon', {
                body: (currentTunnel.subdomain || currentTunnel.tunnel_id) + ' ' + D.formatExpiryCountdown(msLeft) + '. Open LNbitsBox to renew.',
                tag: key,
            });
            if (notification && typeof notification.close === 'function') {
                setTimeout(function () { notification.close(); }, 12000);
            }
            D.markTunnelAlertSent(key);
        } catch (error) {}
    };

    D.setTunnelInvoiceButtonLoading = function (isLoading) {
        D.state.tunnelInvoiceLoading = isLoading;
        const btn = D.el('tunnel-invoice-btn');
        if (!btn) return;
        if (isLoading) {
            btn.disabled = true;
            btn.classList.add('opacity-70', 'cursor-not-allowed');
            btn.innerHTML = '<span class="inline-flex items-center gap-2"><span class="w-3.5 h-3.5 border-2 border-white/70 border-t-transparent rounded-full animate-spin"></span><span>Getting invoice</span></span>';
            return;
        }
        btn.disabled = false;
        btn.classList.remove('opacity-70', 'cursor-not-allowed');
        const hasTunnel = D.state.tunnel && D.state.tunnel.current_tunnel && D.state.tunnel.current_tunnel.tunnel_id;
        btn.textContent = hasTunnel ? 'Add Days' : 'Create Tunnel';
    };

    D.focusTunnelCreate = function () {
        const card = D.el('tunnel-card');
        if (card) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        const input = D.el('tunnel-days-input');
        if (input) input.focus();
    };

    D.toggleTunnelDetails = function () {
        const panel = D.el('tunnel-details');
        const btn = D.el('tunnel-more-btn');
        if (!panel || !btn) return;
        const isHidden = panel.classList.contains('hidden');
        panel.classList.toggle('hidden', !isHidden);
        btn.textContent = isHidden ? 'Less' : 'More';
    };

    D.formatTunnelDate = function (value) {
        if (!value) return '--';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;
        return date.toLocaleString();
    };

    D.setTunnelStatusDot = function (status) {
        const dot = D.el('tunnel-status-dot');
        if (!dot) return;
        if (status === 'active') {
            dot.className = 'w-2.5 h-2.5 rounded-full bg-emerald-400';
        } else if (status === 'pending') {
            dot.className = 'w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse';
        } else {
            dot.className = 'w-2.5 h-2.5 rounded-full bg-gray-600';
        }
    };

    D.renderTunnel = function (data) {
        D.state.tunnel = data;
        const current = data.current_tunnel || {};
        const tunnelStatusRaw = current.status || 'unknown';
        const tunnelStatusLabel = tunnelStatusRaw === 'pending' ? 'pending payment' : tunnelStatusRaw;
        const hasTunnel = !!current.tunnel_id;
        const hasPending = !!data.pending_invoice;

        D.updateTunnelAlertStatus(hasTunnel, current.expires_at);
        D.maybeNotifyTunnelExpiry(current);

        // set https://lnpro.xyz/?id=[session-key] if there is a session key on tunnel-account-link
        if(D.el('tunnel-account-link')) {
            if(data.client_id) {
                const url = 'https://lnpro.xyz/?id=' + encodeURIComponent(data.client_id);
                D.el('tunnel-account-link').textContent = url;
                D.el('tunnel-account-link').href = url;
                D.el('tunnel-account-link').rel = 'noopener noreferrer';
                D.el('tunnel-account-link').target = '_blank';
            } else {
                D.el('tunnel-account-link').textContent = '--';
                D.el('tunnel-account-link').href = '#';
            }
        }
        if (D.el('tunnel-client-id')) D.el('tunnel-client-id').textContent = data.client_id || '--';
        if (D.el('tunnel-remote-port')) D.el('tunnel-remote-port').textContent = current.remote_port || '--';
        if (D.el('tunnel-expires-at')) D.el('tunnel-expires-at').textContent = D.formatTunnelDate(current.expires_at);
        if (D.el('tunnel-service-status')) D.el('tunnel-service-status').textContent = 'service: ' + D.serviceStatusLabel(data.service_status || '--');
        if (D.el('tunnel-status-text')) D.el('tunnel-status-text').textContent = hasTunnel ? tunnelStatusLabel : 'No tunnel yet';
        D.setTunnelStatusDot(tunnelStatusRaw);
        D.setServiceActionVisibility('tunnel', data.service_status || 'inactive', { hasTunnel: hasTunnel });

        const urlEl = D.el('tunnel-public-url');
        const publicUrl = (current.public_url || '').trim();
        if (urlEl) {
            if (publicUrl) {
                urlEl.href = publicUrl;
                urlEl.textContent = publicUrl;
                urlEl.rel = 'noopener noreferrer';
            } else {
                urlEl.href = '#';
                urlEl.textContent = '--';
            }
        }

        D.setTunnelInvoiceButtonLoading(D.state.tunnelInvoiceLoading);
        if (D.el('tunnel-copy-script-btn')) {
            D.el('tunnel-copy-script-btn').disabled = !data.connect_script;
            D.el('tunnel-copy-script-btn').classList.toggle('opacity-50', !data.connect_script);
        }
        if (D.el('tunnel-days-section')) D.el('tunnel-days-section').classList.toggle('hidden', hasPending);
        if (D.el('tunnel-pending-row')) {
            D.el('tunnel-pending-row').classList.toggle('hidden', !hasPending);
            D.el('tunnel-pending-row').classList.toggle('flex', hasPending);
        }
        if (D.el('svc-tunnel-dot')) D.el('svc-tunnel-dot').className = 'w-2.5 h-2.5 rounded-full ' + D.svcColor(data.service_status || 'inactive');
        if (D.el('svc-tunnel-status')) D.el('svc-tunnel-status').textContent = D.serviceStatusLabel(data.service_status || 'unknown');
        ['restart', 'start', 'stop'].forEach(function (verb) {
            const btn = D.el('svc-tunnel-' + verb + '-btn');
            if (!btn) return;
            btn.disabled = !hasTunnel;
            btn.classList.toggle('opacity-50', !hasTunnel);
        });
        if (D.el('svc-tunnel-create-btn')) {
            D.el('svc-tunnel-create-btn').disabled = hasPending;
            D.el('svc-tunnel-create-btn').classList.toggle('opacity-50', hasPending);
        }
        if (!hasPending) {
            D.stopTunnelPoll();
        }
    };

    D.fetchTunnelStatus = async function () {
        try {
            const resp = await fetch('/box/api/tunnel/status');
            if (!resp.ok) return;
            const data = await resp.json();
            D.renderTunnel(data.data || data);
        } catch (error) {
            console.error('Tunnel status fetch failed:', error);
        }
    };

    D.loadInitialTunnelStatus = function () {
        const el = document.getElementById('initial-tunnel-status');
        if (!el || !el.textContent) return;
        try {
            const data = JSON.parse(el.textContent);
            if (data) D.renderTunnel(data);
        } catch (error) {
            console.error('Initial tunnel status parse failed:', error);
        }
    };

    D.renderTunnelInvoiceQr = async function (bolt11) {
        const qrEl = D.el('tunnel-invoice-qr');
        if (!qrEl) return;
        qrEl.replaceChildren();
        if (!bolt11) return;

        try {
            const resp = await fetch('/box/api/qrcode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: bolt11 }),
            });
            if (!resp.ok) {
                throw new Error('QR render failed');
            }
            const blob = await resp.blob();
            const imageUrl = URL.createObjectURL(blob);
            const image = document.createElement('img');
            image.src = imageUrl;
            image.alt = 'Tunnel invoice QR code';
            image.width = 220;
            image.height = 220;
            image.className = 'block';
            image.addEventListener('load', function () {
                URL.revokeObjectURL(imageUrl);
            }, { once: true });
            qrEl.appendChild(image);
        } catch (error) {
            const message = document.createElement('p');
            message.className = 'text-red-400 font-mono text-xs text-center p-4';
            message.textContent = 'Failed to render QR code.';
            qrEl.appendChild(message);
        }
    };

    D.openTunnelInvoiceModal = function (bolt11) {
        const modal = D.el('tunnel-invoice-modal');
        const textarea = D.el('tunnel-invoice-text');
        const status = D.el('tunnel-invoice-status');
        if (!modal || !textarea || !status) return;
        modal.classList.remove('hidden');
        textarea.value = bolt11 || '';
        status.textContent = 'Waiting for payment...';
        D.renderTunnelInvoiceQr(bolt11);
    };

    D.closeTunnelInvoiceModal = function () {
        const modal = D.el('tunnel-invoice-modal');
        if (modal) modal.classList.add('hidden');
        D.stopTunnelPoll();
    };

    D.payPendingTunnelInvoice = function () {
        const pending = D.state.tunnel && D.state.tunnel.pending_invoice;
        if (!pending || !pending.payment_request) return;
        D.openTunnelInvoiceModal(pending.payment_request);
        D.startTunnelPoll();
    };

    D.copyTunnelInvoice = async function () {
        const invoiceEl = D.el('tunnel-invoice-text');
        if (!invoiceEl) return;
        const text = invoiceEl.value;
        if (!text) return;
        await navigator.clipboard.writeText(text);
        const status = D.el('tunnel-invoice-status');
        if (status) {
            status.textContent = 'Copied';
            setTimeout(function () { status.textContent = 'Waiting for payment...'; }, 1500);
        }
    };

    D.stopTunnelPoll = function () {
        if (D.timers.tunnelInvoicePoll) {
            clearInterval(D.timers.tunnelInvoicePoll);
            D.timers.tunnelInvoicePoll = null;
        }
    };

    D.startTunnelPoll = function () {
        if (D.timers.tunnelInvoicePoll) return;
        D.timers.tunnelInvoicePoll = setInterval(async function () {
            try {
                const resp = await fetch('/box/api/tunnel/poll', { method: 'POST' });
                if (!resp.ok) return;
                const payload = await resp.json();
                const data = payload.data || payload;
                D.renderTunnel(data);
                if (payload.paid || data.paid) {
                    const status = D.el('tunnel-invoice-status');
                    if (status) status.textContent = 'Payment confirmed.';
                    setTimeout(function () { D.closeTunnelInvoiceModal(); }, 1200);
                    D.stopTunnelPoll();
                }
            } catch (error) {}
        }, 2500);
    };

    D.openTunnelInvoiceFlow = async function () {
        const daysInput = D.el('tunnel-days-input');
        if (!daysInput) return;
        const days = parseInt(daysInput.value || '0', 10);
        if (!days || days <= 0) {
            D.showNotice('Days must be greater than zero', 'Validation');
            return;
        }
        D.setTunnelInvoiceButtonLoading(true);
        const hasTunnel = D.state.tunnel && D.state.tunnel.current_tunnel && D.state.tunnel.current_tunnel.tunnel_id;
        const endpoint = hasTunnel ? '/box/api/tunnel/renew-invoice' : '/box/api/tunnel/create-invoice';
        try {
            const resp = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ days: days }),
            });
            const payload = await resp.json();
            if (!resp.ok || payload.status !== 'ok') {
                D.showNotice('Error: ' + (payload.message || 'request failed'), 'Error');
                return;
            }
            D.renderTunnel(Object.assign({}, D.state.tunnel || {}, {
                current_tunnel: payload.current_tunnel,
                pending_invoice: payload.invoice,
                connect_script: payload.connect_script,
            }));
            D.openTunnelInvoiceModal(payload.invoice.payment_request);
            D.startTunnelPoll();
        } catch (error) {
            D.showNotice('Invoice request failed', 'Error');
        } finally {
            D.setTunnelInvoiceButtonLoading(false);
        }
    };

    D.copyTunnelScript = async function () {
        const script = D.state.tunnel && D.state.tunnel.connect_script;
        if (!script) return;
        try {
            await navigator.clipboard.writeText(script);
            const btn = D.el('tunnel-copy-script-btn');
            const old = btn.textContent;
            btn.textContent = 'Copied';
            setTimeout(function () { btn.textContent = old; }, 1500);
        } catch (error) {
            D.showNotice('Failed to copy connect script', 'Error');
        }
    };

    D.loadInitialTunnelStatus();
    if (typeof D.fetchTunnelStatus === 'function') {
        D.fetchTunnelStatus();
    }
})();
