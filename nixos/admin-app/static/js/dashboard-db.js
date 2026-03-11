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
        D.el('confirm-title').textContent = 'Download Backup?';
        D.el('confirm-message').textContent = 'LNbits will be stopped while creating the backup. It will be restarted automatically.';
        D.el('confirm-modal').classList.remove('hidden');
        D.el('confirm-btn').onclick = function () {
            D.closeModal();
            D.startDbBackup();
        };
    };

    D.startDbBackup = function () {
        D.setDbBusy(true, 'Creating backup... LNbits is stopping.');
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        document.body.appendChild(iframe);
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/box/api/db/backup';
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrf_token';
        csrfInput.value = document.querySelector('meta[name="csrf-token"]')?.content || '';
        form.appendChild(csrfInput);
        form.target = 'db-backup-frame-' + Date.now();
        iframe.name = form.target;
        document.body.appendChild(form);
        form.submit();
        setTimeout(function () {
            D.setDbBusy(false);
            document.body.removeChild(form);
            setTimeout(function () { document.body.removeChild(iframe); }, 5000);
            D.fetchDbInfo();
        }, 5000);
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

    D.startRestore = async function () {
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
        const formData = new FormData();
        formData.append('file', file);
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
            } else {
                icon.className = 'w-8 h-8 rounded-full mb-3 bg-red-400';
                text.textContent = data.error || 'Restore failed';
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

    D.fetchDbInfo();
})();
