(function () {
  const D = window.LNbitsBoxDashboard;
  if (!D) return;

  const state = {
    pendingMnemonic: '',
  };

  function el(id) {
    return document.getElementById(id);
  }

  function openModal(id) {
    const modal = el(id);
    if (modal) modal.classList.remove('hidden');
  }

  function closeModal(id) {
    const modal = el(id);
    if (modal) modal.classList.add('hidden');
  }

  function setError(message) {
    const errorEl = el('spark-seed-form-error');
    if (!errorEl) return;
    if (message) {
      errorEl.textContent = message;
      errorEl.classList.remove('hidden');
    } else {
      errorEl.textContent = '';
      errorEl.classList.add('hidden');
    }
  }

  function normalizeMnemonic(value) {
    return (value || '').trim().toLowerCase().split(/\s+/).filter(Boolean).join(' ');
  }

  function currentMnemonic() {
    const seedValue = el('spark-seed-value');
    return normalizeMnemonic(seedValue ? seedValue.dataset.seedPhrase || '' : '');
  }

  function validateMnemonic(value) {
    const normalized = normalizeMnemonic(value);
    if (!normalized) return 'Enter a seed phrase.';
    const words = normalized.split(' ');
    if (words.length !== 12) return 'Enter exactly 12 words.';
    if (normalized === currentMnemonic()) return 'This is already the current seed phrase.';
    return '';
  }

  function resetFlow() {
    state.pendingMnemonic = '';
    const input = el('spark-seed-new-input');
    if (input) input.value = '';
    const checkbox = el('spark-seed-backed-up-checkbox');
    if (checkbox) checkbox.checked = false;
    const confirmBtn = el('spark-seed-backup-confirm-btn');
    if (confirmBtn) confirmBtn.disabled = true;
    setError('');
    closeModal('spark-seed-change-modal');
    closeModal('spark-seed-backup-modal');
    D.closeModal();
  }

  async function submitMnemonic(sudoPassword) {
    const actionBtn = el('spark-seed-change-continue-btn');
    const originalHtml = actionBtn ? actionBtn.innerHTML : '';
    if (actionBtn) {
      actionBtn.disabled = true;
      actionBtn.innerHTML = '<span class="inline-flex items-center gap-2"><span class="w-3.5 h-3.5 border-2 border-white/70 border-t-transparent rounded-full animate-spin"></span><span>Updating...</span></span>';
    }

    try {
      const resp = await fetch('/box/api/spark/seed', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mnemonic: state.pendingMnemonic, sudo_password: sudoPassword }),
      });
      const data = await resp.json();
      if (!resp.ok || data.status !== 'ok') {
        if (data.code === 'sudo_required') {
          D.requestSudoPassword('Admin password required', data.message || 'Enter your admin password to replace the Spark wallet seed phrase.', 'Replace Seed Phrase', submitMnemonic);
          return;
        }
        closeModal('spark-seed-backup-modal');
        openModal('spark-seed-change-modal');
        setError(data.message || 'Failed to update the seed phrase.');
        return;
      }

      const seedValue = el('spark-seed-value');
      if (seedValue) {
        seedValue.dataset.seedPhrase = state.pendingMnemonic;
        seedValue.dataset.masked = 'true';
        seedValue.textContent = '••••• ••••• ••••• ••••• ••••• ••••• ••••• ••••• ••••• ••••• ••••• •••••';
      }
      const toggleBtn = el('spark-seed-toggle-btn');
      if (toggleBtn) toggleBtn.textContent = 'Show Seed Phrase';

      resetFlow();
      D.showNotice(data.message || 'Spark seed phrase updated. Spark is restarting automatically.', 'Success');
      if (typeof D.fetchStats === 'function') {
        setTimeout(D.fetchStats, 1200);
      }
    } catch (error) {
      closeModal('spark-seed-backup-modal');
      openModal('spark-seed-change-modal');
      setError('Request failed.');
    } finally {
      if (actionBtn) {
        actionBtn.disabled = false;
        actionBtn.innerHTML = originalHtml;
      }
    }
  }

  function openFinalConfirm() {
    closeModal('spark-seed-backup-modal');
    D.openConfirm({
      title: 'Final confirmation',
      message: 'Are you absolutely sure you want to replace the Spark wallet seed phrase now? This cannot be undone from LNbitsBox.',
      buttonText: 'Replace Seed Phrase',
      requireSudo: true,
      onConfirm: function (sudoPassword) {
        D.closeModal();
        submitMnemonic(sudoPassword);
      },
    });
  }

  const openBtn = el('spark-seed-change-btn');
  const closeBtn = el('spark-seed-change-close-btn');
  const cancelBtn = el('spark-seed-change-cancel-btn');
  const continueBtn = el('spark-seed-change-continue-btn');
  const backupCancelBtn = el('spark-seed-backup-cancel-btn');
  const backupConfirmBtn = el('spark-seed-backup-confirm-btn');
  const backupCheckbox = el('spark-seed-backed-up-checkbox');

  if (openBtn) {
    openBtn.addEventListener('click', function () {
      setError('');
      openModal('spark-seed-change-modal');
      const input = el('spark-seed-new-input');
      if (input) input.focus();
    });
  }

  [closeBtn, cancelBtn].filter(Boolean).forEach(function (button) {
    button.addEventListener('click', function () {
      resetFlow();
    });
  });

  if (continueBtn) {
    continueBtn.addEventListener('click', function () {
      const input = el('spark-seed-new-input');
      const normalized = normalizeMnemonic(input ? input.value : '');
      const error = validateMnemonic(normalized);
      if (error) {
        setError(error);
        return;
      }
      state.pendingMnemonic = normalized;
      setError('');
      closeModal('spark-seed-change-modal');
      openModal('spark-seed-backup-modal');
    });
  }

  if (backupCheckbox && backupConfirmBtn) {
    backupCheckbox.addEventListener('change', function () {
      backupConfirmBtn.disabled = !backupCheckbox.checked;
    });
  }

  if (backupCancelBtn) {
    backupCancelBtn.addEventListener('click', function () {
      closeModal('spark-seed-backup-modal');
      openModal('spark-seed-change-modal');
    });
  }

  if (backupConfirmBtn) {
    backupConfirmBtn.addEventListener('click', function () {
      if (backupConfirmBtn.disabled) return;
      openFinalConfirm();
    });
  }

  document.addEventListener('keydown', function (event) {
    if (event.key !== 'Escape') return;
    if (!el('spark-seed-change-modal')?.classList.contains('hidden')) {
      resetFlow();
      return;
    }
    if (!el('spark-seed-backup-modal')?.classList.contains('hidden')) {
      closeModal('spark-seed-backup-modal');
      openModal('spark-seed-change-modal');
    }
  });
})();
