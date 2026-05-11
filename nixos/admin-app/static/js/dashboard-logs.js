(function () {
    const D = window.LNbitsBoxDashboard;
    const select = document.getElementById('logs-service-select');
    const viewer = document.getElementById('logs-viewer');
    const status = document.getElementById('logs-status');
    const liveToggle = document.getElementById('logs-live-toggle');
    const refreshButton = document.getElementById('logs-refresh-btn');
    const downloadLink = document.getElementById('logs-download-link');

    if (!D || !select || !viewer || !status || !liveToggle || !refreshButton || !downloadLink) return;

    const POLL_MS = 5000;
    D.state.logs = D.state.logs || {};
    D.state.logs.timer = null;
    D.state.logs.requestId = 0;

    function selectedService() {
        return select.value || '';
    }

    function isLiveEnabled() {
        return !!liveToggle.checked;
    }

    function setDownloadHref() {
        const service = encodeURIComponent(selectedService());
        downloadLink.href = '/box/api/logs/' + service + '/download';
    }

    function clearTimer() {
        if (D.state.logs.timer) {
            window.clearTimeout(D.state.logs.timer);
            D.state.logs.timer = null;
        }
    }

    function scheduleNextPoll() {
        clearTimer();
        if (!isLiveEnabled()) return;
        D.state.logs.timer = window.setTimeout(function () {
            loadLogs({ silent: true });
        }, POLL_MS);
    }

    async function loadLogs(options) {
        const opts = options || {};
        const requestId = ++D.state.logs.requestId;
        const service = selectedService();
        const shouldStickToBottom = isLiveEnabled() || viewer.scrollTop + viewer.clientHeight >= viewer.scrollHeight - 24;

        setDownloadHref();
        status.textContent = opts.silent ? 'Updating...' : 'Loading...';
        if (!opts.silent) viewer.textContent = 'Loading...';

        try {
            const response = await fetch('/box/api/logs/' + encodeURIComponent(service) + '?lines=200');
            const payload = await response.json();
            if (requestId !== D.state.logs.requestId) return;

            if (payload.status !== 'ok') {
                throw new Error(payload.message || 'Failed to load logs');
            }

            const data = payload.data || {};
            viewer.textContent = data.content || 'No log entries found for this service.';
            status.textContent = (data.label || 'Service') + ' - ' + (isLiveEnabled() ? 'Live tail on' : 'Snapshot') + ' - ' + new Date().toLocaleTimeString();
            if (shouldStickToBottom) viewer.scrollTop = viewer.scrollHeight;
        } catch (error) {
            if (requestId !== D.state.logs.requestId) return;
            viewer.textContent = 'Unable to load logs.';
            status.textContent = error && error.message ? error.message : 'Unable to load logs.';
        } finally {
            if (requestId === D.state.logs.requestId) scheduleNextPoll();
        }
    }

    select.addEventListener('change', function () {
        loadLogs();
    });

    liveToggle.addEventListener('change', function () {
        if (isLiveEnabled()) {
            loadLogs({ silent: true });
        } else {
            clearTimer();
            status.textContent = 'Live tail paused';
        }
    });

    refreshButton.addEventListener('click', function () {
        loadLogs();
    });

    document.addEventListener('visibilitychange', function () {
        if (document.hidden) {
            clearTimer();
            return;
        }
        loadLogs({ silent: true });
    });

    setDownloadHref();
    loadLogs();
})();
