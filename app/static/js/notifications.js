const Notifications = {
  async refresh() {
    if (!Auth.token) return;
    try {
      const data = await API.get('/api/notifications/');
      const badge = document.getElementById('notifBadge');
      const menu = document.getElementById('notifMenu');
      if (!badge || !menu) return;
      if (data.unread_count > 0) {
        badge.textContent = data.unread_count;
        badge.classList.remove('d-none');
      } else {
        badge.classList.add('d-none');
      }
      menu.innerHTML = data.items.length
        ? data.items
            .map(
              n => `<li><a class="dropdown-item ${n.is_read ? '' : 'fw-bold'}" href="${n.link || '#'}">${n.message}</a></li>`
            )
            .join('') + `<li><hr class="dropdown-divider"></li><li><button class="dropdown-item small" id="notifReadAll">${I18n.t('notifications.readAll')}</button></li>`
        : `<li class="dropdown-item text-muted">${I18n.t('notifications.empty')}</li>`;
      document.getElementById('notifReadAll')?.addEventListener('click', async () => {
        await API.post('/api/notifications/read-all', {});
        this.refresh();
      });
    } catch (e) {
      /* ignore */
    }
  },
};

document.addEventListener('DOMContentLoaded', () => {
  Notifications.refresh();
  setInterval(() => Notifications.refresh(), 15000);
});
window.addEventListener('focus', () => Notifications.refresh());
