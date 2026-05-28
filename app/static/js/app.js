const API = {
  async post(url, body = {}) {
    const res = await fetch(url, {
      method: 'POST',
      headers: Auth.headers(),
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Request failed');
    }
    return res.json();
  },

  async get(url) {
    const res = await fetch(url, { headers: Auth.headers() });
    if (!res.ok) throw new Error('Request failed');
    return res.json();
  },

  async patch(url, body) {
    const res = await fetch(url, {
      method: 'PATCH',
      headers: Auth.headers(),
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Request failed');
    }
    return res.json();
  },

  async delete(url) {
    const res = await fetch(url, { method: 'DELETE', headers: Auth.headers() });
    if (!res.ok) throw new Error('Request failed');
    return res.json().catch(() => ({}));
  },
};

const ChartHelper = {
  instances: {},

  destroy(id) {
    if (this.instances[id]) {
      this.instances[id].destroy();
      delete this.instances[id];
    }
  },

  createLineChart(canvasId, datasets, options = {}) {
    this.destroy(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const gridColor = isDark ? 'rgba(148,163,184,0.2)' : 'rgba(100,116,139,0.2)';
    const textColor = isDark ? '#f1f5f9' : '#1e293b';

    this.instances[canvasId] = new Chart(ctx, {
      type: 'line',
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: options.animate ? 1500 : 600 },
        plugins: {
          legend: { labels: { color: textColor } },
        },
        scales: {
          x: {
            type: 'linear',
            title: { display: true, text: 'x', color: textColor },
            ticks: { color: textColor },
            grid: { color: gridColor },
          },
          y: {
            title: { display: true, text: 'y', color: textColor },
            ticks: { color: textColor },
            grid: { color: gridColor },
          },
        },
        ...options.chartOptions,
      },
    });
    return this.instances[canvasId];
  },

  datasetFromXY(x, y, label, color, fill = false) {
    const data = x.map((xi, i) => ({ x: xi, y: y[i] })).filter(p => p.y !== null);
    return {
      label,
      data,
      borderColor: color,
      backgroundColor: fill ? color.replace('1)', '0.3)') : 'transparent',
      fill,
      tension: 0.3,
      pointRadius: 0,
      borderWidth: 2,
    };
  },
};

window.API = API;
window.ChartHelper = ChartHelper;

window.addEventListener('langchange', () => {
  Object.keys(ChartHelper.instances).forEach(id => {
    const chart = ChartHelper.instances[id];
    if (chart) chart.update();
  });
});
