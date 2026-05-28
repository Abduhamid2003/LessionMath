const Auth = {
  token: localStorage.getItem('token'),
  user: JSON.parse(localStorage.getItem('user') || 'null'),

  init() {
    this.updateUI();
  },

  updateUI() {
    const loginBtn = document.querySelector('.auth-login');
    const profileBtn = document.querySelector('.auth-profile-btn');
    const notifWrap = document.querySelector('.auth-notifications');
    const chatNav = document.querySelector('.auth-nav-chat');

    if (this.token && this.user) {
      loginBtn?.classList.add('d-none');
      profileBtn?.classList.remove('d-none');
      notifWrap?.classList.remove('d-none');
      chatNav?.classList.remove('d-none');
      if (this.user.role === 'admin') this.ensureAdminLink();
      if (this.user.preferred_theme) Theme.apply(this.user.preferred_theme);
      if (this.user.preferred_language) I18n.setLang(this.user.preferred_language, false);
    } else {
      loginBtn?.classList.remove('d-none');
      profileBtn?.classList.add('d-none');
      notifWrap?.classList.add('d-none');
      chatNav?.classList.add('d-none');
    }
  },

  ensureAdminLink() {
    const nav = document.querySelector('#navMenu .navbar-nav');
    if (nav && !document.querySelector('.nav-admin:not(.d-none)')) {
      document.querySelectorAll('.nav-admin').forEach(el => el.classList.remove('d-none'));
      I18n.apply();
    }
  },

  async login(username, password) {
    const form = new FormData();
    form.append('username', username);
    form.append('password', password);
    const res = await fetch('/api/auth/login', { method: 'POST', body: form });
    if (!res.ok) throw new Error('Invalid credentials');
    const data = await res.json();
    this.setSession(data);
    return data;
  },

  async register(payload) {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Registration failed');
    }
    const data = await res.json();
    this.setSession(data);
    return data;
  },

  setSession(data) {
    this.token = data.access_token;
    this.user = data.user;
    localStorage.setItem('token', this.token);
    localStorage.setItem('user', JSON.stringify(this.user));
    this.updateUI();
  },

  logout() {
    this.token = null;
    this.user = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/';
  },

  headers() {
    const h = { 'Content-Type': 'application/json' };
    if (this.token) h.Authorization = `Bearer ${this.token}`;
    return h;
  },
};

window.Auth = Auth;
document.addEventListener('DOMContentLoaded', () => Auth.init());
