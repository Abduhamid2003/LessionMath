async function calculateIntegral() {
  const expression = document.getElementById('expression').value || 'x**2';
  const a = parseFloat(document.getElementById('a').value) || 0;
  const b = parseFloat(document.getElementById('b').value) || 2;
  const method = document.getElementById('method').value || 'all';

  const data = await API.post('/api/math/integral', { expression, a, b, method });

  const plot = data.function_plot;
  const datasets = [
    ChartHelper.datasetFromXY(plot.x, plot.y, 'f(x)', 'rgba(99, 102, 241, 1)'),
    ChartHelper.datasetFromXY(data.area_x, data.area_y, 'Area', 'rgba(139, 92, 246, 0.5)', true),
  ];

  ChartHelper.createLineChart('integralChart', datasets, { animate: true });

  let methodsHtml = '';
  if (data.numerical_methods) {
    methodsHtml = Object.entries(data.numerical_methods)
      .map(([k, v]) => `<span class="badge bg-secondary me-1">${k}: ${v.toFixed(6)}</span>`)
      .join('');
  }

  document.getElementById('integralResult').innerHTML = `
    <div class="result-badge">∫[${a}, ${b}] = ${data.value.toFixed(6)}</div>
    <div class="latex-box mt-2" id="intLatex"></div>
    <div class="mt-2">${methodsHtml}</div>`;
  KatexHelper.renderIntoHtml(document.getElementById('intLatex'), data.latex);
}

async function calculateIndefinite() {
  const expression = document.getElementById('expression').value || 'x**2';
  const data = await API.post('/api/math/integral/indefinite', { expression, order: 1 });

  document.getElementById('integralResult').innerHTML = `
    <div class="result-badge">∫ f(x) dx</div>
    <div class="latex-box mt-2" id="indLatex"></div>`;
  KatexHelper.renderIntoHtml(document.getElementById('indLatex'), data.latex);
}

document.addEventListener('DOMContentLoaded', () => {
  FormulaPad.init('expression');
  document.getElementById('calcIntegralBtn')?.addEventListener('click', calculateIntegral);
  document.getElementById('calcIndefiniteBtn')?.addEventListener('click', calculateIndefinite);
  document.querySelectorAll('[data-integral-tab]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-integral-tab]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const mode = btn.dataset.integralTab;
      document.getElementById('definiteFields').classList.toggle('d-none', mode !== 'definite');
      document.getElementById('calcIntegralBtn').classList.toggle('d-none', mode !== 'definite');
      document.getElementById('calcIndefiniteBtn').classList.toggle('d-none', mode !== 'indefinite');
    });
  });
  calculateIntegral().catch(() => {});
});
