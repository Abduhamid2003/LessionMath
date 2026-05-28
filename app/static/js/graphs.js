const COLORS = [
  'rgba(99, 102, 241, 1)',
  'rgba(239, 68, 68, 1)',
  'rgba(16, 185, 129, 1)',
  'rgba(245, 158, 11, 1)',
  'rgba(139, 92, 246, 1)',
];

async function plotGraph(animate = true) {
  const expression = document.getElementById('expression').value || 'x**2';
  const expression2 = document.getElementById('expression2')?.value?.trim();
  const xMin = parseFloat(document.getElementById('xMin').value) || -10;
  const xMax = parseFloat(document.getElementById('xMax').value) || 10;

  let datasets = [];
  let latexHtml = '';

  if (expression2) {
    const multi = await API.post('/api/math/plot-multi', {
      expressions: [expression, expression2],
      x_min: xMin,
      x_max: xMax,
    });
    multi.series.forEach((s, i) => {
      datasets.push(ChartHelper.datasetFromXY(s.x, s.y, `f${i + 1}(x)`, COLORS[i % COLORS.length]));
      latexHtml += `<div class="latex-box mb-1" id="latex-${i}"></div>`;
      setTimeout(() => KatexHelper.renderIntoHtml(document.getElementById(`latex-${i}`), s.latex), 0);
    });
    const data = multi.series[0];
    if (data.intersections) {
      /* intersections only on first in multi - optional */
    }
  } else {
    const data = await API.post('/api/math/plot', { expression, x_min: xMin, x_max: xMax });
    datasets.push(ChartHelper.datasetFromXY(data.x, data.y, `f(x) = ${data.expression}`, COLORS[0]));
    if (data.intersections?.length) {
      datasets.push({
        label: 'Intersections',
        data: data.intersections,
        backgroundColor: 'rgba(239, 68, 68, 1)',
        pointRadius: 6,
        showLine: false,
      });
    }
    latexHtml = `<div class="latex-box" id="latex-main"></div>`;
    setTimeout(() => KatexHelper.renderIntoHtml(document.getElementById('latex-main'), data.latex), 0);
  }

  ChartHelper.createLineChart('mainChart', datasets, { animate });

  document.getElementById('resultInfo').innerHTML = `
    <div class="result-badge mt-3">${I18n.t('graphs.plot')}</div>
    ${latexHtml}
  `;
}

function setExample(expr) {
  document.getElementById('expression').value = expr;
  plotGraph(true);
}

function saveFavorite() {
  const expression = document.getElementById('expression').value;
  if (!Auth.token) return alert(I18n.t('login.title'));
  API.post('/api/formulas/favorites', { expression, label: 'graph', is_favorite: true })
    .then(() => alert(I18n.t('common.success')))
    .catch(e => alert(e.message));
}

function exportChart() {
  const canvas = document.getElementById('mainChart');
  if (!canvas) return;
  const link = document.createElement('a');
  link.download = 'graph.png';
  link.href = canvas.toDataURL('image/png');
  link.click();
}

document.addEventListener('DOMContentLoaded', () => {
  FormulaPad.init('expression');
  ShareHelper.applyFromUrl([
    { param: 'expr', id: 'expression' },
    { param: 'expr2', id: 'expression2' },
    { param: 'xmin', id: 'xMin' },
    { param: 'xmax', id: 'xMax' },
  ]);
  document.getElementById('plotBtn')?.addEventListener('click', () => plotGraph(true));
  document.getElementById('saveBtn')?.addEventListener('click', saveFavorite);
  document.getElementById('exportBtn')?.addEventListener('click', exportChart);
  document.getElementById('shareBtn')?.addEventListener('click', () =>
    ShareHelper.copyLink([
      { param: 'expr', id: 'expression' },
      { param: 'expr2', id: 'expression2' },
      { param: 'xmin', id: 'xMin' },
      { param: 'xmax', id: 'xMax' },
    ])
  );
  document.querySelectorAll('.example-btn').forEach(btn => {
    btn.addEventListener('click', () => setExample(btn.dataset.expr));
  });
  plotGraph(false);
});
