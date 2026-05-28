let currentTest = null;
let currentAnswers = {};

async function loadLessons() {
  const lessons = await API.get('/api/lessons/');
  const container = document.getElementById('lessonsList');
  if (!container) return;

  container.innerHTML = lessons
    .map(
      l => `
    <div class="col-md-6 col-lg-4" data-aos="fade-up">
      <div class="glass-card feature-card lesson-card p-4" data-id="${l.id}">
        <span class="badge bg-primary mb-2">${l.category}</span>
        <h5 class="lesson-title">${I18n.field(l, 'title')}</h5>
        <p class="text-muted small lesson-content">${I18n.field(l, 'content').substring(0, 120)}...</p>
      </div>
    </div>`
    )
    .join('');

  container.querySelectorAll('.lesson-card').forEach(card => {
    card.addEventListener('click', async () => {
      const lesson = await API.get(`/api/lessons/${card.dataset.id}`);
      const imgs = (lesson.image_urls || [])
        .map(u => `<img src="${u}" class="img-fluid rounded mb-2" style="max-height:200px" alt="">`)
        .join('');
      document.getElementById('lessonModalBody').innerHTML = `
        <h4>${I18n.field(lesson, 'title')}</h4>
        ${imgs ? `<div class="mb-3">${imgs}</div>` : ''}
        <p>${I18n.field(lesson, 'content')}</p>`;
      new bootstrap.Modal(document.getElementById('lessonModal')).show();
    });
  });
}

async function loadTests() {
  const tests = await API.get('/api/tests/');
  const container = document.getElementById('testsList');
  if (!container) return;

  container.innerHTML = tests
    .map(
      t => `
    <div class="glass-card p-3 mb-3 d-flex justify-content-between align-items-center">
      <div>
        <h6>${I18n.field(t, 'title')}</h6>
        <small class="text-muted">${t.question_count} questions · ${t.max_score} pts</small>
      </div>
      <button class="btn btn-primary btn-sm start-test" data-id="${t.id}">${I18n.t('learning.start')}</button>
    </div>`
    )
    .join('');

  container.querySelectorAll('.start-test').forEach(btn => {
    btn.addEventListener('click', () => startTest(btn.dataset.id));
  });
}

async function startTest(testId) {
  currentTest = await API.get(`/api/tests/${testId}`);
  currentAnswers = {};
  const area = document.getElementById('testArea');
  area.classList.remove('d-none');

  area.innerHTML = `
    <h4>${I18n.field(currentTest, 'title')}</h4>
    ${currentTest.questions
      .map(
        (q, idx) => `
      <div class="glass-card p-3 mb-3 question-block" data-qid="${q.id}">
        <p><strong>${idx + 1}.</strong> ${I18n.field(q, 'question')}</p>
        ${(I18n.lang === 'tg' ? q.options_tg : I18n.lang === 'en' ? (q.options_en || q.options_ru) : q.options_ru)
          .map(
            (opt, oi) => `
          <div class="form-check">
            <input class="form-check-input" type="radio" name="q${q.id}" value="${oi}" id="q${q.id}_${oi}">
            <label class="form-check-label" for="q${q.id}_${oi}">${opt}</label>
          </div>`
          )
          .join('')}
        <button class="btn btn-sm btn-outline-secondary mt-2 hint-btn" data-hint="${I18n.field(q, 'hint')}">
          <i class="bi bi-lightbulb"></i> Hint
        </button>
      </div>`
      )
      .join('')}
    <button class="btn btn-primary" id="submitTest">${I18n.t('learning.submit')}</button>
  `;

  area.querySelectorAll('input[type=radio]').forEach(inp => {
    inp.addEventListener('change', () => {
      currentAnswers[parseInt(inp.name.replace('q', ''))] = parseInt(inp.value);
    });
  });

  area.querySelectorAll('.hint-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      if (btn.dataset.hint) alert(btn.dataset.hint);
    });
  });

  document.getElementById('submitTest').addEventListener('click', submitTest);
  area.scrollIntoView({ behavior: 'smooth' });
}

async function submitTest() {
  if (!Auth.token) return alert(I18n.t('login.title'));
  const result = await API.post(`/api/tests/${currentTest.id}/submit`, { answers: currentAnswers });
  document.getElementById('testResult').innerHTML = `
    <div class="glass-card p-4 text-center" data-aos="zoom-in">
      <h3>${I18n.t('learning.score')}: ${result.score} / ${result.max_score}</h3>
      <div class="display-4 text-primary">${result.percentage}%</div>
    </div>`;
}

async function openLessonFromQuery() {
  const id = new URLSearchParams(location.search).get('lesson');
  if (!id) return;
  const lesson = await API.get(`/api/lessons/${id}`);
  document.getElementById('lessonModalBody').innerHTML = `
    <h4>${I18n.field(lesson, 'title')}</h4>
    ${(lesson.image_urls || []).map(u => `<img src="${u}" class="img-fluid rounded mb-2" style="max-height:200px">`).join('')}
    <p>${I18n.field(lesson, 'content')}</p>`;
  new bootstrap.Modal(document.getElementById('lessonModal')).show();
}

document.addEventListener('DOMContentLoaded', () => {
  loadLessons().catch(console.error);
  loadTests().catch(console.error);
  openLessonFromQuery().catch(() => {});
  document.getElementById('learnCheckBtn')?.addEventListener('click', async () => {
    const data = await API.post('/api/math/check-derivative', {
      expression: document.getElementById('learnPracticeExpr').value,
      user_answer: document.getElementById('learnPracticeAns').value,
    });
    document.getElementById('learnPracticeResult').innerHTML = data.correct
      ? `<div class="alert alert-success">${I18n.t('common.success')}</div>`
      : `<div class="alert alert-warning">${I18n.t('learning.tryAgain')}</div>`;
  });
});

window.addEventListener('langchange', () => {
  loadLessons();
  loadTests();
});
