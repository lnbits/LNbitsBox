(function () {
    const D = window.LNbitsBoxDashboard;
    if (!D) return;

    function el(id) {
        return document.getElementById(id);
    }

    function hasRecoveryUi() {
        return !!el('recovery-card');
    }

    function formatDate(value) {
        if (!value) return 'Never';
        const date = typeof value === 'number' ? new Date(value * 1000) : new Date(value);
        if (Number.isNaN(date.getTime())) return 'Unknown';
        return date.toLocaleString();
    }

    function formatBytes(bytes) {
        if (typeof D.formatBytes === 'function') {
            return D.formatBytes(bytes);
        }
        if (!bytes) return '0 B';
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
        return (bytes / Math.pow(1024, index)).toFixed(1) + ' ' + units[index];
    }

    function scheduleSummary(schedule) {
        if (!schedule || !schedule.enabled) return 'Disabled';
        return 'Every ' + schedule.interval_hours + 'h';
    }

    function selectedRestoreComponents() {
        return Array.from(document.querySelectorAll('[data-restore-component]:checked')).map(function (input) {
            return input.value;
        });
    }

    function selectedRestoreSource() {
        return document.querySelector('input[name="restore-source"]:checked')?.value || 'upload';
    }

    function backupDownloadUrl(filename) {
        return '/box/api/recovery/backups/' + encodeURIComponent(filename);
    }

    D.renderSavedBackups = function (backups) {
        const container = el('recovery-saved-backups');
        const localSelect = el('restore-local-backup');
        if (container) {
            container.innerHTML = '';
        }
        if (localSelect) {
            localSelect.innerHTML = '<option value="">Choose a saved backup</option>';
        }
        if (!backups || !backups.length) {
            if (container) {
                container.innerHTML = '<div class="recovery-helper-text">No saved backups on this box yet.</div>';
            }
            return;
        }
        backups.forEach(function (backup) {
            if (container) {
                const row = document.createElement('div');
                row.className = 'recovery-saved-row';
                row.innerHTML =
                    '<div class="min-w-0">' +
                    '<div class="text-sm font-mono text-ln-text truncate">' + backup.filename + '</div>' +
                    '<div class="text-xs font-mono text-ln-muted">' + formatDate(backup.modified_at) + ' · ' + formatBytes(backup.size) + '</div>' +
                    '</div>' +
                    '<div class="flex items-center gap-2 shrink-0">' +
                    '<a class="text-ln-muted hover:text-ln-pink text-xs font-mono uppercase tracking-wider transition-colors px-3 py-2 border border-ln-border rounded-lg hover:border-ln-pink/30" href="' + backupDownloadUrl(backup.filename) + '">Download</a>' +
                    '</div>';
                container.appendChild(row);
            }
            if (localSelect) {
                const option = document.createElement('option');
                option.value = backup.filename;
                option.textContent = backup.filename + ' · ' + formatDate(backup.modified_at);
                localSelect.appendChild(option);
            }
        });
    };

    D.fetchSavedBackups = async function () {
        try {
            const resp = await fetch('/box/api/recovery/backups');
            if (!resp.ok) return [];
            const payload = await resp.json();
            const backups = payload.backups || payload.data?.backups || [];
            D.renderSavedBackups(backups);
            return backups;
        } catch (error) {
            console.error('Saved backups fetch failed:', error);
            return [];
        }
    };

    D.setRecoveryBusy = function (busy, text) {
        const status = el('recovery-status');
        const statusText = el('recovery-status-text');
        if (!status || !statusText) return;
        status.classList.toggle('hidden', !busy);
        statusText.textContent = text || 'Processing...';
        ['recovery-download-btn', 'recovery-save-btn', 'recovery-restore-btn', 'recovery-schedule-save-btn'].forEach(function (id) {
            const button = el(id);
            if (!button) return;
            button.disabled = busy;
            button.classList.toggle('opacity-50', busy);
        });
    };

    D.fetchRecoveryStatus = async function () {
        if (!hasRecoveryUi()) return;
        try {
            const resp = await fetch('/box/api/recovery/status');
            if (!resp.ok) return;
            const payload = await resp.json();
            const data = payload.data || payload;
            const lastBackup = data.last_backup || null;
            const lastValidation = data.last_validation || null;
            const schedule = data.schedule || {};
            const savedBackups = data.saved_backups || [];

            D.setText('recovery-last-backup', lastBackup ? formatDate(lastBackup.created_at) : 'No backup yet');
            D.setText('recovery-seed-status', data.spark_seed_present ? 'Saved' : 'Missing');
            D.setText('recovery-validation-status', lastValidation ? lastValidation.status : 'Unknown');
            D.setText('recovery-tunnel-status', data.tunnel_ready ? 'Ready' : 'Missing');
            D.setText('recovery-schedule-summary', scheduleSummary(schedule));
            D.setText('recovery-schedule-result', schedule.last_result ? schedule.last_result.message : 'No scheduled backup has run yet.');

            const actionList = el('recovery-actions');
            if (actionList) {
                actionList.innerHTML = '';
                (data.recommended_actions || []).forEach(function (item) {
                    const li = document.createElement('li');
                    li.textContent = item;
                    actionList.appendChild(li);
                });
            }
            D.renderSavedBackups(savedBackups);

            if (el('recovery-schedule-hours')) {
                el('recovery-schedule-hours').value = schedule.interval_hours || 24;
                el('recovery-schedule-type').value = schedule.backup_type || 'full';
                el('recovery-schedule-enabled').checked = !!schedule.enabled;
                if (schedule.passphrase === 'configured' && el('recovery-schedule-passphrase')) {
                    el('recovery-schedule-passphrase').placeholder = 'Configured. Enter a new password to rotate it.';
                }
            }
        } catch (error) {
            console.error('Recovery status fetch failed:', error);
        }
    };

    D.downloadRecoveryBackup = function () {
        const passphrase = el('recovery-passphrase')?.value || '';
        const backupType = el('recovery-backup-type')?.value || 'full';
        if (!passphrase) {
            D.showNotice('Enter a backup password first.', 'Validation');
            return;
        }
        D.setRecoveryBusy(true, 'Preparing encrypted backup for download...');
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        document.body.appendChild(iframe);
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/box/api/recovery/backup/download';
        form.target = 'recovery-download-frame-' + Date.now();
        iframe.name = form.target;
        [
            ['csrf_token', document.querySelector('meta[name="csrf-token"]')?.content || ''],
            ['backup_type', backupType],
            ['passphrase', passphrase],
        ].forEach(function (pair) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = pair[0];
            input.value = pair[1];
            form.appendChild(input);
        });
        document.body.appendChild(form);
        form.submit();
        setTimeout(function () {
            D.setRecoveryBusy(false);
            form.remove();
            setTimeout(function () { iframe.remove(); }, 5000);
            D.fetchRecoveryStatus();
        }, 4000);
    };

    D.saveRecoveryBackup = async function () {
        const passphrase = el('recovery-passphrase')?.value || '';
        const backupType = el('recovery-backup-type')?.value || 'full';
        if (!passphrase) {
            D.showNotice('Enter a backup password first.', 'Validation');
            return;
        }
        D.setRecoveryBusy(true, 'Saving encrypted backup on this box...');
        try {
            const resp = await fetch('/box/api/recovery/backup/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    backup_type: backupType,
                    passphrase: passphrase,
                }),
            });
            const data = await resp.json();
            if (resp.ok && data.status === 'ok') {
                D.showNotice(data.message, 'Backup Saved');
                D.fetchRecoveryStatus();
                D.fetchSavedBackups();
            } else {
                D.showNotice(data.message || 'Backup save failed.', 'Error');
            }
        } catch (error) {
            D.showNotice('Backup save failed: ' + error.message, 'Error');
        } finally {
            D.setRecoveryBusy(false);
        }
    };

    D.openRestoreModal = function () {
        const modal = el('restore-modal');
        if (!modal) return;
        modal.classList.remove('hidden');
        D.showRestoreView('restore-form');
        D.setText('restore-compatibility', 'Validate to inspect');
        D.setText('restore-manifest-summary', 'No archive checked yet');
        if (el('restore-file')) el('restore-file').value = '';
        if (el('restore-local-backup')) el('restore-local-backup').value = '';
        el('restore-issues')?.classList.add('hidden');
        if (el('restore-issues')) el('restore-issues').textContent = '';
        if (el('restore-components')) el('restore-components').innerHTML = '';
        el('restore-components-wrap')?.classList.add('hidden');
        if (el('restore-result-details')) el('restore-result-details').textContent = '';
        D.updateRestoreSourceUi();
        D.fetchSavedBackups();
    };

    D.closeRestoreModal = function () {
        const modal = el('restore-modal');
        if (modal) modal.classList.add('hidden');
    };

    D.showRestoreView = function (id) {
        ['restore-form', 'restore-progress', 'restore-result'].forEach(function (viewId) {
            const node = el(viewId);
            if (node) node.classList.toggle('hidden', viewId !== id);
        });
    };

    D.updateRestoreSourceUi = function () {
        const source = selectedRestoreSource();
        const uploadFields = el('restore-upload-fields');
        const localFields = el('restore-local-fields');
        if (uploadFields) uploadFields.classList.toggle('hidden', source !== 'upload');
        if (localFields) localFields.classList.toggle('hidden', source !== 'local');
    };

    D.validateRestoreBackup = async function () {
        const fileInput = el('restore-file');
        const localBackup = el('restore-local-backup')?.value || '';
        const passphrase = el('restore-passphrase')?.value || '';
        if (selectedRestoreSource() === 'upload' && !fileInput?.files?.length) {
            D.showNotice('Please select an encrypted backup file.', 'Validation');
            return;
        }
        if (selectedRestoreSource() === 'local' && !localBackup) {
            D.showNotice('Please choose a saved backup from this box.', 'Validation');
            return;
        }
        if (!passphrase) {
            D.showNotice('Enter the backup password before validating.', 'Validation');
            return;
        }
        const formData = new FormData();
        if (selectedRestoreSource() === 'upload') {
            formData.append('file', fileInput.files[0]);
        } else {
            formData.append('local_backup', localBackup);
        }
        formData.append('passphrase', passphrase);
        D.showRestoreView('restore-progress');
        D.setText('restore-progress-text', 'Validating encrypted backup...');
        try {
            const resp = await fetch('/box/api/recovery/restore/validate', { method: 'POST', body: formData });
            const data = await resp.json();
            D.showRestoreView('restore-form');
            const issues = data.issues || data.data?.issues || [];
            const manifest = data.manifest || data.data?.manifest || {};
            const compatibility = data.compatibility || data.data?.compatibility || {};
            const components = data.components || data.data?.components || {};

            D.setText('restore-compatibility', compatibility.message || 'Unknown');
            D.setText('restore-manifest-summary', (manifest.backup_type || 'backup') + ' from ' + (manifest.created_at || 'unknown date'));

            const issueBox = el('restore-issues');
            if (issueBox) {
                if (issues.length) {
                    issueBox.textContent = issues.join('\n');
                    issueBox.classList.remove('hidden');
                } else {
                    issueBox.textContent = '';
                    issueBox.classList.add('hidden');
                }
            }

            const componentsWrap = el('restore-components-wrap');
            const componentsBox = el('restore-components');
            if (componentsBox) {
                componentsBox.innerHTML = '';
                Object.keys(components).forEach(function (component) {
                    const label = document.createElement('label');
                    label.className = 'flex items-start gap-2 bg-ln-surface border border-ln-border rounded-lg p-3';
                    label.innerHTML = '<input type="checkbox" checked data-restore-component value="' + component + '" class="mt-0.5 rounded border-ln-border bg-ln-card text-ln-pink focus:ring-ln-pink/40">' +
                        '<span class="text-sm font-mono text-ln-text">' + component + '<br><span class="text-xs text-ln-muted">' + components[component].count + ' file(s)</span></span>';
                    componentsBox.appendChild(label);
                });
            }
            if (componentsWrap) {
                componentsWrap.classList.toggle('hidden', !Object.keys(components).length);
            }
            if (resp.ok && data.status !== 'error') {
                D.showNotice('Backup validation succeeded. Select the components you want to restore.', 'Validation');
            } else {
                D.showNotice((compatibility.message || 'Validation failed.') + (issues.length ? ' ' + issues.join(' ') : ''), 'Validation');
            }
        } catch (error) {
            D.showRestoreView('restore-form');
            D.showNotice('Validation failed: ' + error.message, 'Error');
        }
    };

    D.startRestore = async function () {
        const fileInput = el('restore-file');
        const localBackup = el('restore-local-backup')?.value || '';
        const passphrase = el('restore-passphrase')?.value || '';
        const components = selectedRestoreComponents();
        if (selectedRestoreSource() === 'upload' && !fileInput?.files?.length) {
            D.showNotice('Please select an encrypted backup file.', 'Validation');
            return;
        }
        if (selectedRestoreSource() === 'local' && !localBackup) {
            D.showNotice('Please choose a saved backup from this box.', 'Validation');
            return;
        }
        if (!passphrase) {
            D.showNotice('Enter the backup password before restoring.', 'Validation');
            return;
        }
        const formData = new FormData();
        if (selectedRestoreSource() === 'upload') {
            formData.append('file', fileInput.files[0]);
        } else {
            formData.append('local_backup', localBackup);
        }
        formData.append('passphrase', passphrase);
        components.forEach(function (component) {
            formData.append('components', component);
        });
        D.showRestoreView('restore-progress');
        D.setText('restore-progress-text', 'Restoring selected components...');
        try {
            const resp = await fetch('/box/api/recovery/restore', { method: 'POST', body: formData });
            const data = await resp.json();
            D.showRestoreView('restore-result');
            const icon = el('restore-result-icon');
            const text = el('restore-result-text');
            const details = el('restore-result-details');
            if (resp.ok && data.status === 'ok') {
                icon.className = 'w-8 h-8 rounded-full mb-3 bg-emerald-400';
                text.textContent = data.message;
                text.className = 'font-mono text-sm mb-1 text-emerald-400';
                const report = data.report || data.data?.report || {};
                const lines = [];
                (report.checks || []).forEach(function (check) {
                    lines.push((check.ok ? 'OK' : 'WARN') + '  ' + (check.label || check.component));
                });
                if (report.compatibility?.message) lines.push(report.compatibility.message);
                details.textContent = lines.join('\n');
                D.fetchRecoveryStatus();
            } else {
                icon.className = 'w-8 h-8 rounded-full mb-3 bg-red-400';
                text.textContent = data.message || 'Restore failed';
                text.className = 'font-mono text-sm mb-1 text-red-400';
                details.textContent = (data.report?.compatibility?.message || '');
            }
        } catch (error) {
            D.showRestoreView('restore-result');
            el('restore-result-icon').className = 'w-8 h-8 rounded-full mb-3 bg-red-400';
            const text = el('restore-result-text');
            text.textContent = 'Restore failed: ' + error.message;
            text.className = 'font-mono text-sm mb-1 text-red-400';
        }
    };

    D.saveRecoverySchedule = async function () {
        const payload = {
            enabled: !!el('recovery-schedule-enabled')?.checked,
            interval_hours: Number(el('recovery-schedule-hours')?.value || 24),
            backup_type: el('recovery-schedule-type')?.value || 'full',
            passphrase: el('recovery-schedule-passphrase')?.value || '',
        };
        D.setRecoveryBusy(true, 'Saving encrypted backup schedule...');
        try {
            const resp = await fetch('/box/api/recovery/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await resp.json();
            if (resp.ok && data.status === 'ok') {
                D.showNotice(data.message, 'Schedule Saved');
                D.fetchRecoveryStatus();
            } else {
                D.showNotice(data.message || 'Schedule update failed.', 'Error');
            }
        } catch (error) {
            D.showNotice('Schedule update failed: ' + error.message, 'Error');
        } finally {
            D.setRecoveryBusy(false);
        }
    };

    if (hasRecoveryUi()) {
        document.querySelectorAll('input[name="restore-source"]').forEach(function (input) {
            input.addEventListener('change', D.updateRestoreSourceUi);
        });
        D.fetchRecoveryStatus();
        D.fetchSavedBackups();
    }
})();
