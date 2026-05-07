(function () {
  const D = window.LNbitsBoxDashboard;
  if (!D) return;

  function el(id) {
    return D.el ? D.el(id) : document.getElementById(id);
  }

  function closeFirstModal() {
    const modal = el('factory-reset-first-modal');
    if (modal) modal.classList.add('hidden');
  }

  function closeSecondModal() {
    const modal = el('factory-reset-second-modal');
    if (modal) modal.classList.add('hidden');
    const checkbox = el('factory-reset-confirm-checkbox');
    const button = el('factory-reset-confirm-btn');
    if (checkbox) checkbox.checked = false;
    if (button) {
      button.disabled = true;
      button.textContent = 'Proceed with Factory Reset';
    }
  }

  D.openFactoryResetFirstModal = function () {
    closeSecondModal();
    const modal = el('factory-reset-first-modal');
    if (modal) modal.classList.remove('hidden');
  };

  D.closeFactoryResetModals = function () {
    closeFirstModal();
    closeSecondModal();
  };

  D.openFactoryResetSecondModal = function () {
    closeFirstModal();
    const modal = el('factory-reset-second-modal');
    if (modal) modal.classList.remove('hidden');
  };

  D.submitFactoryReset = async function () {
    const button = el('factory-reset-confirm-btn');
    if (!button || button.disabled) return;

    const originalLabel = button.textContent;
    button.disabled = true;
    button.innerHTML = '<span class="inline-flex items-center gap-2"><span class="w-3.5 h-3.5 border-2 border-white/70 border-t-transparent rounded-full animate-spin"></span><span>Resetting...</span></span>';

    try {
      const resp = await fetch('/box/api/factory-reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ acknowledged: true })
      });
      const data = await resp.json();
      if (data.status === 'ok') {
        D.closeFactoryResetModals();
        D.showNotice(data.message, 'Factory Reset Started');
        const delay = data.data?.delay_ms || 3000;
        const redirect = data.data?.redirect || '/';
        window.setTimeout(function () {
          window.location.href = redirect;
        }, delay);
        return;
      }
      D.showNotice(data.message || 'Factory reset failed.', 'Error');
    } catch (error) {
      D.showNotice('Factory reset failed.', 'Error');
    } finally {
      button.disabled = true;
      button.textContent = originalLabel;
      const checkbox = el('factory-reset-confirm-checkbox');
      if (checkbox) {
        button.disabled = !checkbox.checked;
      }
    }
  };

  document.addEventListener('change', function (event) {
    if (event.target?.id !== 'factory-reset-confirm-checkbox') return;
    const button = el('factory-reset-confirm-btn');
    if (button) button.disabled = !event.target.checked;
  });
})();
