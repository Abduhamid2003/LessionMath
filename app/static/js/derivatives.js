let tangentAnimTimer = null;

function showDerivError(msg) {
  const el = document.getElementById('derivResult');
  if (el) el.innerHTML = `<div class="alert alert-danger small">${msg}</div>`;
}

async function calculateDerivative() {
  const expression = (document.getElementById('expression')?.value || 'x**2').trim();
  const order = parseInt(document.getElementById('order')?.value, 10) || 1;
  const resultEl = document.getElementById('derivResult');
  const stepsEl = document.getElementById('stepsBox');

  try {
    if (resultEl) resultEl.innerHTML = `<div class="text-muted small">${I18n.t('common.loading')}</div>`;

    const data = await API.post('/api/math/derivative', { expression, order });

    if (!data?.function_plot?.x || !data?.derivative_plot?.x) {
      throw new Error('No plot data');
    }

    const datasets = [
      ChartHelper.datasetFromXY(data.function_plot.x, data.function_plot.y, 'f(x)', 'rgba(99, 102, 241, 1)'),
      ChartHelper.datasetFromXY(data.derivative_plot.x, data.derivative_plot.y, "f'(x)", 'rgba(239, 68, 68, 1)'),
    ];

    const chart = ChartHelper.createLineChart('derivChart', datasets, { animate: true });
    if (chart) setTimeout(() => chart.resize(), 100);

    if (resultEl) {
      resultEl.innerHTML = `
        <div class="result-badge">f<sup>(${order})</sup>(x)</div>
        <div class="latex-box mt-2" id="derivLatex"></div>
        <button type="button" class="btn btn-sm btn-outline-secondary mt-2" id="pdfBtn">${I18n.t('common.export')}</button>`;
      if (window.KatexHelper && data.latex) {
        KatexHelper.renderIntoHtml(document.getElementById('derivLatex'), data.latex);
      }
      document.getElementById('pdfBtn')?.addEventListener('click', async () => {
        const res = await fetch('/api/math/derivative/pdf', {
          method: 'POST',
          headers: Auth.headers(),
          body: JSON.stringify({ expression, order }),
        });
        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'derivative.pdf';
        a.click();
      });
    }

    if (stepsEl && data.steps) {
      KatexHelper.renderSteps(stepsEl, data.steps);
    }
  } catch (e) {
    console.error(e);
    showDerivError(e.message || I18n.t('common.error'));
  }
}

async function showTangent(x0Override) {
  const expression = (document.getElementById('expression')?.value || 'x**2').trim();
  const x0Val = document.getElementById('x0')?.value;
  const x0 = x0Override !== undefined && x0Override !== null ? x0Override : parseFloat(x0Val) || 0;

  try {
    const data = await API.post('/api/math/tangent', { expression, x0 });

    const datasets = [
      ChartHelper.datasetFromXY(data.plot.x, data.plot.y, 'f(x)', 'rgba(99, 102, 241, 1)'),
      ChartHelper.datasetFromXY(data.tangent.tangent_x, data.tangent.tangent_y, 'Tangent', 'rgba(16, 185, 129, 1)'),
      {
        label: `(${x0.toFixed(2)}, ${data.tangent.y0.toFixed(3)})`,
        data: [{ x: x0, y: data.tangent.y0 }],
        backgroundColor: 'rgba(245, 158, 11, 1)',
        pointRadius: 8,
        showLine: false,
      },
    ];

    const chart = ChartHelper.createLineChart('derivChart', datasets, { animate: false });
    if (chart) setTimeout(() => chart.resize(), 100);

    const resultEl = document.getElementById('derivResult');
    if (resultEl) {
      resultEl.innerHTML = `
        <div class="result-badge">${data.tangent.tangent_equation}</div>
        <p class="text-muted mt-2">slope = ${data.tangent.slope.toFixed(4)}</p>`;
    }
  } catch (e) {
    showDerivError(e.message || I18n.t('common.error'));
  }
}

function startTangentAnimation() {
  if (tangentAnimTimer) clearInterval(tangentAnimTimer);
  const slider = document.getElementById('x0Anim');
  if (!slider) return showTangent();
  let x = parseFloat(slider.min) || -3;
  tangentAnimTimer = setInterval(() => {
    const x0Input = document.getElementById('x0');
    if (x0Input) x0Input.value = x;
    showTangent(x).catch(() => {});
    x += 0.2;
    if (x > parseFloat(slider.max)) x = parseFloat(slider.min);
  }, 400);
}

function stopTangentAnimation() {
  if (tangentAnimTimer) {
    clearInterval(tangentAnimTimer);
    tangentAnimTimer = null;
  }
}

function setExample(expr) {
  const input = document.getElementById('expression');
  if (input) input.value = expr;
  calculateDerivative();
}

window.calculateDerivative = calculateDerivative;
window.showTangent = showTangent;

document.addEventListener('DOMContentLoaded', () => {
  FormulaPad.init('expression');

  document.getElementById('calcDerivBtn')?.addEventListener('click', calculateDerivative);
  document.getElementById('tangentBtn')?.addEventListener('click', () => showTangent());
  document.getElementById('animStartBtn')?.addEventListener('click', startTangentAnimation);
  document.getElementById('animStopBtn')?.addEventListener('click', stopTangentAnimation);

  document.querySelectorAll('.example-btn').forEach(btn => {
    btn.addEventListener('click', () => setExample(btn.dataset.expr));
  });

  setTimeout(() => calculateDerivative(), 300);
});
