const ShareHelper = {
  applyFromUrl(keys) {
    const params = new URLSearchParams(window.location.search);
    keys.forEach(({ param, id }) => {
      const el = document.getElementById(id);
      const v = params.get(param);
      if (el && v !== null) el.value = v;
    });
  },

  buildUrl(keys) {
    const params = new URLSearchParams();
    keys.forEach(({ param, id }) => {
      const el = document.getElementById(id);
      if (el?.value) params.set(param, el.value);
    });
    const qs = params.toString();
    return qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
  },

  copyLink(keys) {
    const url = window.location.origin + this.buildUrl(keys);
    navigator.clipboard?.writeText(url).then(() => alert(I18n.t('common.success'))).catch(() => prompt('URL:', url));
  },
};

window.ShareHelper = ShareHelper;
