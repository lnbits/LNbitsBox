(function () {
  const sidebar = document.getElementById('admin-sidebar');
  const toggle = document.getElementById('admin-sidebar-toggle');
  const closeButton = document.getElementById('admin-sidebar-close');
  const backdrop = document.getElementById('admin-sidebar-backdrop');
  const updateLinks = document.querySelectorAll('[data-update-link]');

  function closeSidebar() {
    document.body.classList.remove('sidebar-open');
  }

  if (sidebar && toggle && backdrop) {
    toggle.addEventListener('click', function () {
      document.body.classList.toggle('sidebar-open');
    });

    backdrop.addEventListener('click', closeSidebar);
    closeButton?.addEventListener('click', closeSidebar);

    sidebar.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', closeSidebar);
    });
  }

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') closeSidebar();
  });

  if (updateLinks.length) {
    fetch('/box/api/update/check')
      .then(function (resp) {
        if (!resp.ok) return null;
        return resp.json();
      })
      .then(function (data) {
        if (!data || !data.update_available) return;
        updateLinks.forEach(function (link) {
          link.classList.add('visible');
        });
      })
      .catch(function () {});
  }
})();
