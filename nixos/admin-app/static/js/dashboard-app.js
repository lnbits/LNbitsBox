(function () {
  const D = window.LNbitsBoxDashboard;

  function bindClick(id, handler, options) {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('click', function (event) {
      if (options && options.preventDefault) event.preventDefault();
      handler(event, el);
    });
  }

  bindClick('tunnel-alert-enable-btn', function () { D.enableTunnelExpiryAlerts(); });
  bindClick('tunnel-invoice-btn', function () { D.openTunnelInvoiceFlow(); });
  bindClick('tunnel-pay-invoice-btn', function () { D.payPendingTunnelInvoice(); });
  bindClick('tunnel-more-btn', function () { D.toggleTunnelDetails(); }, { preventDefault: true });
  bindClick('tunnel-copy-script-btn', function () { D.copyTunnelScript(); });
  bindClick('tunnel-invoice-close-btn', function () { D.closeTunnelInvoiceModal(); });
  bindClick('tunnel-invoice-copy-btn', function () { D.copyTunnelInvoice(); });
  bindClick('tor-copy-btn', function () { D.copyOnion(); });

  bindClick('wifi-open-scan-btn', function () { D.openWifiScan(); });
  bindClick('wifi-close-btn', function () { D.closeWifiModal(); });
  bindClick('wifi-cancel-btn', function () { D.closeWifiModal(); });
  bindClick('wifi-back-btn', function () { D.showScanList(); });
  bindClick('wifi-try-another-btn', function () { D.showScanList(); });
  bindClick('wifi-done-btn', function () { D.closeWifiModal(); });
  bindClick('db-backup-btn', function () { D.confirmDbBackup(); });
  bindClick('db-restore-btn', function () { D.openRestoreModal(); });
  bindClick('restore-close-btn', function () { D.closeRestoreModal(); });
  bindClick('restore-cancel-btn', function () { D.closeRestoreModal(); });
  bindClick('restore-confirm-btn', function () { D.startRestore(); });
  bindClick('restore-result-close-btn', function () { D.closeRestoreModal(); });
  bindClick('update-check-btn', function () { D.checkForUpdate(); });
  bindClick('update-now-btn', function () { D.confirmUpdate(); });
  bindClick('confirm-cancel-btn', function () { D.closeModal(); });
  bindClick('notice-close-btn', function () { D.closeNoticeModal(); });

  document.querySelectorAll('[data-confirm-action]').forEach(function (button) {
    button.addEventListener('click', function () {
      D.confirmAction(button.dataset.confirmAction, button.dataset.confirmMessage || 'Are you sure?', button.id);
    });
  });

  document.querySelectorAll('[data-run-action]').forEach(function (button) {
    button.addEventListener('click', function () {
      D.executeAction(button.dataset.runAction, button.id);
    });
  });

  document.addEventListener('click', function (event) {
    const networkButton = event.target.closest('[data-wifi-ssid]');
    if (!networkButton) return;
    D.selectWifiNetwork(decodeURIComponent(networkButton.dataset.wifiSsid), decodeURIComponent(networkButton.dataset.wifiFlags || ''));
  });

  const wifiForm = document.getElementById('wifi-connect-form');
  if (wifiForm) {
    wifiForm.addEventListener('submit', function (event) {
      event.preventDefault();
      D.connectToWifi();
    });
  }
})();
