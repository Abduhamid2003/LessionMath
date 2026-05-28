const KatexHelper = {
  render(el, latex, displayMode = false) {
    if (!el || !window.katex) return;
    try {
      katex.render(latex, el, { throwOnError: false, displayMode });
    } catch (e) {
      el.textContent = latex;
    }
  },

  renderIntoHtml(container, latex) {
    if (!container) return;
    const span = document.createElement('span');
    container.innerHTML = '';
    container.appendChild(span);
    this.render(span, latex, true);
  },

  renderSteps(container, steps) {
    if (!container) return;
    container.innerHTML = (steps || [])
      .map((s, i) => {
        const id = `step-${i}-${Date.now()}`;
        return `<div class="mb-2"><strong>${i + 1}.</strong> <span id="${id}"></span></div>`;
      })
      .join('');
    (steps || []).forEach((s, i) => {
      const el = container.querySelectorAll('span[id^="step-"]')[i];
      if (el) this.render(el, s, true);
    });
  },
};

window.KatexHelper = KatexHelper;
