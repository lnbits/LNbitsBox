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
        return 'Backing up every ' + schedule.interval_hours + 'h';
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

    function parseBackupTime(value) {
        const date = typeof value === 'number' ? new Date(value * 1000) : new Date(value);
        return Number.isNaN(date.getTime()) ? null : date;
    }

    function bucketSavedBackups(backups) {
        const now = Date.now();
        const dayMs = 24 * 60 * 60 * 1000;
        const buckets = [
            { label: 'Last 24 hours', items: [] },
            { label: 'Last week', items: [] },
            { label: 'Last 4 weeks', items: [] },
            { label: 'Older', items: [] },
        ];

        (backups || []).forEach(function (backup) {
            const modified = parseBackupTime(backup.modified_at);
            const age = modified ? now - modified.getTime() : Number.POSITIVE_INFINITY;
            if (age <= dayMs) {
                buckets[0].items.push(backup);
            } else if (age <= 7 * dayMs) {
                buckets[1].items.push(backup);
            } else if (age <= 28 * dayMs) {
                buckets[2].items.push(backup);
            } else {
                buckets[3].items.push(backup);
            }
        });

        return buckets.filter(function (bucket) {
            return bucket.items.length > 0;
        });
    }

    function savedBackupRowHtml(backup) {
        return '' +
            '<div class="recovery-saved-row">' +
            '<div class="min-w-0">' +
            '<div class="text-sm font-mono text-ln-text truncate">' + backup.filename + '</div>' +
            '<div class="text-xs font-mono text-ln-muted">' + formatDate(backup.modified_at) + ' · ' + formatBytes(backup.size) + '</div>' +
            '</div>' +
            '<div class="flex items-center gap-2 shrink-0">' +
            '<a class="text-ln-muted hover:text-ln-pink text-xs font-mono uppercase tracking-wider transition-colors px-3 py-2 border border-ln-border rounded-lg hover:border-ln-pink/30" href="' + backupDownloadUrl(backup.filename) + '">Download</a>' +
            '</div>' +
            '</div>';
    }

    function devModeSampleBackups() {
        const now = Date.now();
        const hour = 60 * 60 * 1000;
        const day = 24 * hour;
        return [
            { filename: 'lnbitsbox-recovery-full-20260318-1015.zip', modified_at: new Date(now - (2 * hour)).toISOString(), size: 26624 },
            { filename: 'lnbitsbox-recovery-full-20260318-0640.zip', modified_at: new Date(now - (6 * hour)).toISOString(), size: 26602 },
            { filename: 'lnbitsbox-recovery-full-20260317-2210.zip', modified_at: new Date(now - (12 * hour)).toISOString(), size: 26631 },
            { filename: 'lnbitsbox-recovery-full-20260316-0900.zip', modified_at: new Date(now - (2 * day)).toISOString(), size: 26588 },
            { filename: 'lnbitsbox-recovery-full-20260314-0815.zip', modified_at: new Date(now - (4 * day)).toISOString(), size: 26619 },
            { filename: 'lnbitsbox-recovery-full-20260312-0730.zip', modified_at: new Date(now - (6 * day)).toISOString(), size: 26648 },
            { filename: 'lnbitsbox-recovery-full-20260308-0700.zip', modified_at: new Date(now - (10 * day)).toISOString(), size: 26608 },
            { filename: 'lnbitsbox-recovery-full-20260303-0700.zip', modified_at: new Date(now - (15 * day)).toISOString(), size: 26622 },
            { filename: 'lnbitsbox-recovery-full-20260225-0700.zip', modified_at: new Date(now - (21 * day)).toISOString(), size: 26597 },
            { filename: 'lnbitsbox-recovery-full-20260210-0700.zip', modified_at: new Date(now - (36 * day)).toISOString(), size: 26604 },
        ];
    }

    function displayBackups(backups) {
        if ((!backups || !backups.length) && D.root?.dataset.devMode === 'true') {
            return devModeSampleBackups();
        }
        return backups || [];
    }

    const SCHEDULE_PASSCODE_MASK = '••••••••';

    function syncScheduledPassphraseField(schedule) {
        const field = el('recovery-schedule-passphrase');
        if (!field) return;
        const hasStoredPassphrase = schedule && schedule.passphrase === 'configured';
        field.dataset.hasStoredPassphrase = hasStoredPassphrase ? 'true' : 'false';
        if (hasStoredPassphrase) {
            field.value = SCHEDULE_PASSCODE_MASK;
            field.placeholder = 'Stored locally in a root-only config file';
        } else {
            field.value = '';
            field.placeholder = 'Stored locally in a root-only config file';
        }
    }

    D.renderSavedBackups = function (backups) {
        const container = el('recovery-saved-backups');
        const localSelect = el('restore-local-backup');
        const countLabel = el('recovery-saved-backups-count');
        const section = el('recovery-saved-backups-section');
        if (container) {
            container.innerHTML = '';
        }
        if (countLabel) {
            const total = backups && backups.length ? backups.length : 0;
            countLabel.textContent = total === 1 ? '1 backup' : total + ' backups';
        }
        if (section && backups && backups.length) {
            section.open = D.root?.dataset.devMode === 'true';
        }
        if (localSelect) {
            localSelect.innerHTML = '<option value="">Choose a saved backup</option>';
        }
        if (!backups || !backups.length) {
            if (container) {
                container.innerHTML = '<div class="recovery-helper-text">No saved backups yet.</div>';
            }
            return;
        }

        if (container) {
            container.innerHTML = bucketSavedBackups(backups).map(function (bucket) {
                const count = bucket.items.length === 1 ? '1 backup' : bucket.items.length + ' backups';
                return '' +
                    '<section class="recovery-history-group is-collapsed" data-history-group>' +
                    '<button type="button" class="recovery-history-toggle" data-history-toggle>' +
                    '<span class="recovery-history-heading">' +
                    '<span class="recovery-callout-title">' + bucket.label + '</span>' +
                    '<span class="recovery-history-count">' + count + '</span>' +
                    '</span>' +
                    '<span class="recovery-history-chevron" aria-hidden="true">' +
                    '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
                    '<path d="M6 8l4 4 4-4"></path>' +
                    '</svg>' +
                    '</span>' +
                    '</button>' +
                    '<div class="recovery-history-preview">' +
                    '<div class="recovery-saved-list">' + bucket.items.map(savedBackupRowHtml).join('') + '</div>' +
                    '<div class="recovery-history-fade" aria-hidden="true"></div>' +
                    '</div>' +
                    '</section>';
            }).join('');

            container.querySelectorAll('[data-history-toggle]').forEach(function (button) {
                button.addEventListener('click', function () {
                    const group = button.closest('[data-history-group]');
                    if (!group) return;
                    group.classList.toggle('is-collapsed');
                });
            });
        }

        backups.forEach(function (backup) {
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
            const backups = displayBackups(payload.backups || payload.data?.backups || []);
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
            const savedBackups = displayBackups(data.saved_backups || []);

            D.setText('recovery-last-backup', lastBackup ? formatDate(lastBackup.created_at) : 'No backup yet');
            D.setText('recovery-seed-status', data.spark_seed_present ? 'Saved' : 'Missing');
            D.setText('recovery-validation-status', lastValidation ? lastValidation.status : 'Unknown');
            D.setText('recovery-tunnel-status', data.tunnel_ready ? 'Ready' : 'Missing');
            D.setText('recovery-schedule-summary', scheduleSummary(schedule));
            D.setText('recovery-schedule-result', schedule.last_result ? schedule.last_result.message : 'No scheduled backup has run yet.');

            D.renderSavedBackups(savedBackups);

            if (el('recovery-schedule-hours')) {
                el('recovery-schedule-hours').value = schedule.interval_hours || 24;
                el('recovery-schedule-enabled').checked = !!schedule.enabled;
                syncScheduledPassphraseField(schedule);
            }
        } catch (error) {
            console.error('Recovery status fetch failed:', error);
        }
    };

    D.downloadRecoveryBackup = function () {
        const passphrase = el('recovery-passphrase')?.value || '';
        const backupType = 'full';
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
        const backupType = 'full';
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
        el('restore-validation-panel')?.classList.add('hidden');
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
            el('restore-validation-panel')?.classList.remove('hidden');

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
        const passphraseField = el('recovery-schedule-passphrase');
        const hasStoredPassphrase = passphraseField?.dataset.hasStoredPassphrase === 'true';
        const passphraseValue = passphraseField?.value || '';
        const payload = {
            enabled: !!el('recovery-schedule-enabled')?.checked,
            interval_hours: Number(el('recovery-schedule-hours')?.value || 24),
            backup_type: 'full',
            passphrase: hasStoredPassphrase && passphraseValue === SCHEDULE_PASSCODE_MASK ? '' : passphraseValue,
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
        el('recovery-schedule-passphrase')?.addEventListener('focus', function (event) {
            const field = event.currentTarget;
            if (field.dataset.hasStoredPassphrase === 'true' && field.value === SCHEDULE_PASSCODE_MASK) {
                field.value = '';
            }
        });
        document.querySelectorAll('input[name="restore-source"]').forEach(function (input) {
            input.addEventListener('change', D.updateRestoreSourceUi);
        });
        D.fetchRecoveryStatus();
        D.fetchSavedBackups();
    }
})();
