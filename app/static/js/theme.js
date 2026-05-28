const Theme = {
  current: localStorage.getItem('theme') || 'light',

  init() {
    this.apply(this.current);
    const btn = document.getElementById('themeToggle');
    if (btn) {
      btn.addEventListener('click', () => this.toggle());
    }
  },

  apply(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.style.colorScheme = theme;
    this.current = theme;
    localStorage.setItem('theme', theme);
    const icon = document.querySelector('#themeToggle i');
    if (icon) {
      icon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon-stars';
    }
    if (window.Auth?.token) {
      fetch('/api/auth/preferences', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${window.Auth.token}`,
        },
        body: JSON.stringify({ preferred_theme: theme }),
      }).catch(() => {});
    }
  },

  toggle() {
    const next = this.current === 'light' ? 'dark' : 'light';
    document.body.style.transition = 'background-color 0.4s ease, color 0.4s ease';
    this.apply(next);
  },
};

document.addEventListener('DOMContentLoaded', () => Theme.init());
