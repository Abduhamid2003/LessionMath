const Calc = {
  expr: '',
  mode: 'numeric',
  history: [],

  init() {
    this.history = JSON.parse(localStorage.getItem('calcHistory') || '[]');
    this.bindModeTabs();
    this.bindKeypad();
    this.bindActions();
    this.renderHistory();
    FormulaPad.init('calcExprInput');
  },

  bindModeTabs() {
    document.querySelectorAll('[data-calc-mode]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-calc-mode]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.mode = btn.dataset.calcMode;
        document.querySelectorAll('[data-calc-panel]').forEach(p => {
          p.classList.toggle('d-none', p.dataset.calcPanel !== this.mode);
        });
        document.getElementById('calcXRow')?.classList.toggle('d-none', this.mode === 'numeric');
      });
    });
  },

  append(token) {
    const input = document.getElementById('calcExprInput');
    if (!input) return;
    const start = input.selectionStart ?? input.value.length;
    const end = input.selectionEnd ?? input.value.length;
    input.value = input.value.slice(0, start) + token + input.value.slice(end);
    input.focus();
    this.updateDisplay(input.value);
  },

  updateDisplay(val) {
    const el = document.getElementById('calcDisplay');
    if (el) el.textContent = val || '0';
  },

  bindKeypad() {
    document.querySelectorAll('[data-calc-key]').forEach(btn => {
      btn.addEventListener('click', () => this.append(btn.dataset.calcKey));
    });
    document.getElementById('calcClear')?.addEventListener('click', () => {
      document.getElementById('calcExprInput').value = '';
      this.updateDisplay('');
    });
    document.getElementById('calcBackspace')?.addEventListener('click', () => {
      const input = document.getElementById('calcExprInput');
      input.value = input.value.slice(0, -1);
      this.updateDisplay(input.value);
    });
    document.getElementById('calcExprInput')?.addEventListener('input', e => this.updateDisplay(e.target.value));
  },

  bindActions() {
    document.getElementById('calcEvaluate')?.addEventListener('click', () => this.evaluate());
    document.getElementById('calcClearHistory')?.addEventListener('click', () => {
      this.history = [];
      localStorage.setItem('calcHistory', '[]');
      this.renderHistory();
    });
  },

  getExpression() {
    return document.getElementById('calcExprInput')?.value.trim() || '';
  },

  pushHistory(entry) {
    this.history.unshift(entry);
    this.history = this.history.slice(0, 20);
    localStorage.setItem('calcHistory', JSON.stringify(this.history));
    this.renderHistory();
  },

  renderHistory() {
    const el = document.getElementById('calcHistory');
    if (!el) return;
    el.innerHTML = this.history.length
      ? this.history
          .map(
            h => `<button type="button" class="list-group-item list-group-item-action calc-history-item" data-expr="${this.escapeAttr(h.expr)}">
            <small class="text-muted">${h.mode}</small><br>${this.escapeHtml(h.expr)}<br><strong>= ${h.result}</strong>
          </button>`
          )
          .join('')
      : `<p class="text-muted small p-2">${I18n.t('calculator.noHistory')}</p>`;
    el.querySelectorAll('.calc-history-item').forEach(btn => {
      btn.addEventListener('click', () => {
        document.getElementById('calcExprInput').value = btn.dataset.expr;
        this.updateDisplay(btn.dataset.expr);
      });
    });
  },

  async evaluate() {
    const expr = this.getExpression();
    if (!expr) return;

    const resultEl = document.getElementById('calcResult');
    resultEl.innerHTML = `<div class="text-muted">${I18n.t('common.loading')}</div>`;

    try {
      let data;
      let label;

      if (this.mode === 'numeric') {
        data = await API.post('/api/math/evaluate-numeric', { expression: expr });
        label = data.value;
        resultEl.innerHTML = `
          <div class="calc-result-value">${this.formatNum(data.value)}</div>
          <div class="latex-box mt-2" id="calcLatex"></div>
          <p class="text-muted small mt-2">= ${this.escapeHtml(data.simplified)}</p>`;
        KatexHelper.renderIntoHtml(document.getElementById('calcLatex'), data.latex);
      } else if (this.mode === 'function') {
        const x = parseFloat(document.getElementById('calcX').value) || 0;
        data = await API.post('/api/math/evaluate-function', { expression: expr, x });
        label = `f(${x}) = ${data.value}`;
        resultEl.innerHTML = `
          <div class="calc-result-value">f(${x}) = ${this.formatNum(data.value)}</div>
          <div class="chart-container calc-mini-chart mt-3"><canvas id="calcMiniChart"></canvas></div>`;
        if (data.plot) {
          ChartHelper.createLineChart(
            'calcMiniChart',
            [ChartHelper.datasetFromXY(data.plot.x, data.plot.y, 'f(x)', 'rgba(99, 102, 241, 1)')],
            { animate: true }
          );
        }
      } else if (this.mode === 'derivative') {
        const x = parseFloat(document.getElementById('calcX').value) || 0;
        data = await API.post('/api/math/calculator/derivative-at', { expression: expr, x });
        label = `f'(${x}) = ${data.slope}`;
        resultEl.innerHTML = `
          <div class="calc-result-value">f'(${x}) = ${this.formatNum(data.slope)}</div>
          <p class="text-muted">f(${x}) = ${this.formatNum(data.y_at_x)}</p>
          <div class="latex-box" id="calcLatex"></div>`;
        KatexHelper.renderIntoHtml(document.getElementById('calcLatex'), data.latex);
      }

      this.pushHistory({ expr, result: String(label), mode: this.mode });
    } catch (e) {
      resultEl.innerHTML = `<div class="alert alert-danger">${e.message}</div>`;
    }
  },

  formatNum(n) {
    if (Math.abs(n) > 1e6 || (Math.abs(n) < 1e-4 && n !== 0)) return Number(n).toExponential(6);
    return Number(n).toLocaleString(undefined, { maximumFractionDigits: 10 });
  },

  escapeHtml(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  },

  escapeAttr(s) {
    return String(s).replace(/"/g, '&quot;');
  },
};

document.addEventListener('DOMContentLoaded', () => Calc.init());
