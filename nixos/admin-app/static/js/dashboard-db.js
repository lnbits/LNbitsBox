(function () {
    const D = window.LNbitsBoxDashboard;

    D.fetchDbInfo = async function () {
        try {
            const resp = await fetch('/box/api/db/info');
            if (!resp.ok) return;
            const data = await resp.json();
            if (data.size !== undefined) {
                D.el('db-size').textContent = D.formatBytes(data.size);
            }
        } catch (error) {
            console.error('DB info fetch failed:', error);
        }
    };

    D.setDbBusy = function (busy, text) {
        const status = D.el('db-status');
        const buttons = D.el('db-buttons');
        if (busy) {
            status.classList.remove('hidden');
            D.el('db-status-text').textContent = text || 'Processing...';
            buttons.querySelectorAll('button').forEach(function (button) {
                button.disabled = true;
                button.classList.add('opacity-50');
            });
        } else {
            status.classList.add('hidden');
            buttons.querySelectorAll('button').forEach(function (button) {
                button.disabled = false;
                button.classList.remove('opacity-50');
            });
        }
    };

    D.confirmDbBackup = function () {
        D.openConfirm({
            title: 'Download Backup?',
            message: 'LNbits will be stopped while creating the backup. It will be restarted automatically.',
            buttonText: 'Download Backup',
            requireSudo: true,
            onConfirm: function (sudoPassword) {
                D.closeModal();
                D.startDbBackup(sudoPassword);
            },
        });
    };

    D.startDbBackup = async function (sudoPassword) {
        D.setDbBusy(true, 'Creating backup... LNbits is stopping.');
        try {
            const resp = await fetch('/box/api/db/backup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sudo_password: sudoPassword }),
            });

            if (!resp.ok) {
                const data = await resp.json().catch(function () { return {}; });
                D.setDbBusy(false);
                if (data.code === 'sudo_required') {
                    D.requestSudoPassword('Admin password required', data.message || 'Enter your admin password to continue.', 'Download Backup', D.startDbBackup);
                    return;
                }
                D.showNotice(data.error || data.message || 'Backup failed.', 'Error');
                return;
            }

            const blob = await resp.blob();
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'lnbits-backup.zip';
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(url);
        } catch (error) {
            D.showNotice('Backup failed: ' + error.message, 'Error');
        } finally {
            D.setDbBusy(false);
            D.fetchDbInfo();
        }
    };

    D.openRestoreModal = function () {
        D.el('restore-modal').classList.remove('hidden');
        D.el('restore-file').value = '';
        D.showRestoreView('restore-form');
    };

    D.closeRestoreModal = function () {
        D.el('restore-modal').classList.add('hidden');
    };

    D.showRestoreView = function (id) {
        ['restore-form', 'restore-progress', 'restore-result'].forEach(function (viewId) {
            D.el(viewId).classList.toggle('hidden', viewId !== id);
        });
    };

    D.startRestore = async function (sudoPassword) {
        const fileInput = D.el('restore-file');
        if (!fileInput.files || fileInput.files.length === 0) {
            D.showNotice('Please select a backup file.', 'Validation');
            return;
        }
        const file = fileInput.files[0];
        if (!file.name.endsWith('.zip')) {
            D.showNotice('Please select a .zip file.', 'Validation');
            return;
        }
        D.showRestoreView('restore-progress');
        const submitRestore = async function (passwordValue) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('sudo_password', passwordValue);
            try {
                const resp = await fetch('/box/api/db/restore', { method: 'POST', body: formData });
                const data = await resp.json();
                D.showRestoreView('restore-result');
                const icon = D.el('restore-result-icon');
                const text = D.el('restore-result-text');
                if (resp.ok && data.status === 'ok') {
                    icon.className = 'w-8 h-8 rounded-full mb-3 bg-emerald-400';
                    text.textContent = data.message;
                    text.className = 'font-mono text-sm mb-1 text-emerald-400';
                    D.fetchDbInfo();
                } else if (data.code === 'sudo_required') {
                    D.showRestoreView('restore-form');
                    D.requestSudoPassword('Restore Database', data.message || 'Enter your admin password to restore the LNbits database.', 'Restore', D.startRestore);
                } else {
                    icon.className = 'w-8 h-8 rounded-full mb-3 bg-red-400';
                    text.textContent = data.error || data.message || 'Restore failed';
                    text.className = 'font-mono text-sm mb-1 text-red-400';
                }
            } catch (error) {
                D.showRestoreView('restore-result');
                D.el('restore-result-icon').className = 'w-8 h-8 rounded-full mb-3 bg-red-400';
                const text = D.el('restore-result-text');
                text.textContent = 'Request failed: ' + error.message;
                text.className = 'font-mono text-sm mb-1 text-red-400';
            }
        };

        if (sudoPassword) {
            await submitRestore(sudoPassword);
            return;
        }

        D.requestSudoPassword('Restore Database', 'Enter your admin password to restore the LNbits database.', 'Restore', submitRestore);
    };

    D.fetchDbInfo();
})();
