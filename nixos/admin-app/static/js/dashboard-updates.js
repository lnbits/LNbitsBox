(function () {
    const D = window.LNbitsBoxDashboard;
    D.state.updateReleaseTag = '';
    D.timers.updatePollInterval = null;
    D.timers.updateReconnectInterval = null;

    D.showUpdateSection = function (id) {
        ['update-available', 'update-progress', 'update-done'].forEach(function (sectionId) {
            D.el(sectionId).classList.toggle('hidden', sectionId !== id);
        });
    };

    D.checkForUpdate = async function () {
        const btn = D.el('update-check-btn');
        const status = D.el('update-check-status');
        btn.disabled = true;
        status.textContent = 'Checking...';
        try {
            const resp = await fetch('/box/api/update/check');
            if (!resp.ok) {
                status.textContent = 'Check failed';
                btn.disabled = false;
                return;
            }
            const data = await resp.json();
            D.el('update-current-version').textContent = 'v' + data.current_version;
            if (data.update_available) {
                D.state.updateReleaseTag = data.release_tag;
                D.el('update-latest-version').textContent = 'v' + data.latest_version;
                D.el('update-release-notes').textContent = data.release_notes || 'No release notes.';
                D.showUpdateSection('update-available');
                D.el('update-check-section').classList.add('hidden');
            } else {
                status.textContent = 'Up to date';
                setTimeout(function () { status.textContent = ''; }, 3000);
            }
        } catch (error) {
            status.textContent = 'Check failed';
        }
        btn.disabled = false;
    };

    D.confirmUpdate = function () {
        D.el('confirm-title').textContent = 'Start System Update?';
        D.el('confirm-message').textContent = 'This will download and activate a new system version. Services will briefly restart.';
        D.el('confirm-modal').classList.remove('hidden');
        D.el('confirm-btn').onclick = function () {
            D.closeModal();
            D.startUpdate();
        };
    };

    D.startUpdate = async function () {
        D.showUpdateSection('update-progress');
        D.el('update-log').textContent = '';
        D.el('update-progress-status').textContent = 'Starting update...';
        try {
            const resp = await fetch('/box/api/update/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ release_tag: D.state.updateReleaseTag }),
            });
            const data = await resp.json();
            if (data.status !== 'started') {
                D.el('update-progress-status').textContent = 'Error: ' + (data.message || 'Unknown');
                return;
            }
        } catch (error) {
            D.el('update-progress-status').textContent = 'Failed to start update';
            return;
        }
        D.pollUpdateStatus();
        D.timers.updatePollInterval = setInterval(D.pollUpdateStatus, 2000);
    };

    D.pollUpdateStatus = async function () {
        try {
            const resp = await fetch('/box/api/update/status');
            if (!resp.ok) throw new Error('status fetch failed');
            const data = await resp.json();
            const logEl = D.el('update-log');
            if (data.log_lines && data.log_lines.length > 0) {
                logEl.textContent = data.log_lines.join('\n');
                logEl.scrollTop = logEl.scrollHeight;
            }
            const statusLabels = {
                idle: 'Waiting for system to start update. This may take a moment...',
                downloading: 'Downloading updates. Please wait...',
                activating: 'Activating new system. Services will restart shortly...',
            };
            if (data.status === 'success') {
                clearInterval(D.timers.updatePollInterval);
                D.timers.updatePollInterval = null;
                D.el('update-done-dot').className = 'w-2.5 h-2.5 rounded-full bg-emerald-400';
                D.el('update-done-text').textContent = 'Update complete! Services have been restarted.';
                D.el('update-done-text').className = 'text-sm font-mono text-emerald-400';
                D.showUpdateSection('update-done');
                setTimeout(function () { location.reload(); }, 3000);
            } else if (data.status === 'failed') {
                clearInterval(D.timers.updatePollInterval);
                D.timers.updatePollInterval = null;
                D.el('update-done-dot').className = 'w-2.5 h-2.5 rounded-full bg-red-400';
                D.el('update-done-text').textContent = 'Update failed. Check logs above for details.';
                D.el('update-done-text').className = 'text-sm font-mono text-red-400';
                D.showUpdateSection('update-done');
            } else {
                D.el('update-progress-status').textContent = statusLabels[data.status] || data.status;
            }
        } catch (error) {
            D.el('update-progress-status').textContent = 'Reconnecting... (services restarting)';
            D.startReconnect();
        }
    };

    D.startReconnect = function () {
        if (D.timers.updateReconnectInterval) return;
        clearInterval(D.timers.updatePollInterval);
        D.timers.updatePollInterval = null;
        D.timers.updateReconnectInterval = setInterval(async function () {
            try {
                const resp = await fetch('/box/api/update/status');
                if (resp.ok) {
                    clearInterval(D.timers.updateReconnectInterval);
                    D.timers.updateReconnectInterval = null;
                    D.pollUpdateStatus();
                    D.timers.updatePollInterval = setInterval(D.pollUpdateStatus, 2000);
                }
            } catch (error) {}
        }, 3000);
    };

    (async function initUpdateCard() {
        try {
            const resp = await fetch('/box/api/update/status');
            if (resp.ok) {
                const data = await resp.json();
                if (data.status === 'downloading' || data.status === 'activating') {
                    D.showUpdateSection('update-progress');
                    D.pollUpdateStatus();
                    D.timers.updatePollInterval = setInterval(D.pollUpdateStatus, 2000);
                } else if (data.status === 'success') {
                    D.el('update-done-dot').className = 'w-2.5 h-2.5 rounded-full bg-emerald-400';
                    D.el('update-done-text').textContent = 'The last update completed successfully.';
                    D.el('update-done-text').className = 'text-sm font-mono text-emerald-400';
                    D.showUpdateSection('update-done');
                } else if (data.status === 'failed') {
                    D.el('update-done-dot').className = 'w-2.5 h-2.5 rounded-full bg-red-400';
                    D.el('update-done-text').textContent = 'Last update failed. Check logs for details.';
                    D.el('update-done-text').className = 'text-sm font-mono text-red-400';
                    D.showUpdateSection('update-done');
                }
            }
        } catch (error) {}
        try {
            const resp = await fetch('/box/api/update/check');
            if (resp.ok) {
                const data = await resp.json();
                D.el('update-current-version').textContent = 'v' + data.current_version;
            }
        } catch (error) {}
    })();
})();
