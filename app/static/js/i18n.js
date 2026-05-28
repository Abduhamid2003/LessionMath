const I18n = {
  lang: localStorage.getItem('lang') || 'ru',
  strings: {},

  async init() {
    await this.load(this.lang);
    this.apply();
    this.bindLangButtons();
  },

  async load(lang) {
    try {
      const res = await fetch(`/static/locales/${lang}.json`);
      this.strings = await res.json();
      this.lang = lang;
      localStorage.setItem('lang', lang);
      document.documentElement.lang = lang;
    } catch (e) {
      console.error('i18n load failed', e);
    }
  },

  t(key) {
    return this.strings[key] || key;
  },

  apply() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const text = this.t(key);
      if (el.tagName === 'INPUT' && el.placeholder !== undefined) {
        el.placeholder = text;
      } else {
        el.textContent = text;
      }
    });
    document.title = this.t('app.title');
  },

  async setLang(lang, persistPreference = true) {
    await this.load(lang);
    this.apply();
    document.querySelectorAll('.lang-switch [data-lang]').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.lang === lang);
    });
    window.dispatchEvent(new CustomEvent('langchange', { detail: { lang } }));

    // Persist preference for logged-in users so navigation won't reset language.
    if (persistPreference && window.Auth?.token && window.Auth?.user) {
      try {
        const res = await fetch('/api/auth/preferences', {
          method: 'PATCH',
          headers: Auth.headers(),
          body: JSON.stringify({ preferred_language: lang }),
        });
        if (res.ok) {
          const updated = await res.json();
          Auth.user = updated;
          localStorage.setItem('user', JSON.stringify(updated));
        } else {
          // Fallback: at least keep local copy
          Auth.user.preferred_language = lang;
          localStorage.setItem('user', JSON.stringify(Auth.user));
        }
      } catch (e) {
        Auth.user.preferred_language = lang;
        localStorage.setItem('user', JSON.stringify(Auth.user));
      }
    }
  },

  bindLangButtons() {
    document.querySelectorAll('.lang-switch [data-lang]').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.lang === this.lang);
      btn.addEventListener('click', () => this.setLang(btn.dataset.lang));
    });
  },

  field(obj, field) {
    const suffix = this.lang === 'tg' ? '_tg' : this.lang === 'en' ? '_en' : '_ru';
    return obj[field + suffix] || obj[field + '_ru'] || obj[field + '_en'] || '';
  },
};

document.addEventListener('DOMContentLoaded', () => I18n.init());
