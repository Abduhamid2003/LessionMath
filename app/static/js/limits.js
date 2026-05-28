async function computeLimit() {
  const expression = document.getElementById('expression').value || 'sin(x)/x';
  const point = parseFloat(document.getElementById('point').value) || 0;
  const direction = document.getElementById('direction').value || 'both';

  const data = await API.post('/api/math/limit', { expression, point, direction });
  const plot = await API.post('/api/math/plot', { expression, x_min: point - 5, x_max: point + 5 });

  ChartHelper.createLineChart(
    'limitChart',
    [ChartHelper.datasetFromXY(plot.x, plot.y, 'f(x)', 'rgba(99, 102, 241, 1)')],
    { animate: true }
  );

  const el = document.getElementById('limitResult');
  el.innerHTML = `<div class="result-badge">lim = ${data.value}</div><div class="latex-box mt-2" id="limitLatex"></div>`;
  KatexHelper.renderIntoHtml(document.getElementById('limitLatex'), data.latex);
}

async function computeTaylor() {
  const expression = document.getElementById('expression').value || 'exp(x)';
  const x0 = parseFloat(document.getElementById('taylorX0').value) || 0;
  const order = parseInt(document.getElementById('taylorOrder').value) || 5;

  const data = await API.post('/api/math/taylor', { expression, x0, order });

  ChartHelper.createLineChart(
    'limitChart',
    [
      ChartHelper.datasetFromXY(data.function_plot.x, data.function_plot.y, 'f(x)', 'rgba(99, 102, 241, 1)'),
      ChartHelper.datasetFromXY(data.taylor_plot.x, data.taylor_plot.y, 'Taylor', 'rgba(239, 68, 68, 1)'),
    ],
    { animate: true }
  );

  document.getElementById('limitResult').innerHTML = `
    <div class="result-badge">T<sub>${order}</sub>(x) around ${x0}</div>
    <div class="latex-box mt-2" id="taylorLatex"></div>`;
  KatexHelper.renderIntoHtml(document.getElementById('taylorLatex'), data.latex);
}

document.addEventListener('DOMContentLoaded', () => {
  FormulaPad.init('expression');
  ShareHelper.applyFromUrl([
    { param: 'expr', id: 'expression' },
    { param: 'point', id: 'point' },
  ]);
  document.getElementById('limitBtn')?.addEventListener('click', computeLimit);
  document.getElementById('taylorBtn')?.addEventListener('click', computeTaylor);
  document.getElementById('shareBtn')?.addEventListener('click', () =>
    ShareHelper.copyLink([
      { param: 'expr', id: 'expression' },
      { param: 'point', id: 'point' },
    ])
  );
  computeLimit().catch(() => {});
});
