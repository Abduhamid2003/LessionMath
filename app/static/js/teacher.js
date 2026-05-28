const Teacher = {
  editingLessonId: null,
  currentTestId: null,
  lessonImages: [],
  currentTestQuestions: [],

  async init() {
    if (!Auth.token || !['teacher', 'admin'].includes(Auth.user?.role)) {
      location.href = '/login';
      return;
    }
    this.bindTabs();
    this.bindLessons();
    this.bindTests();
    this.bindClasses();
    await this.loadClasses();
    await this.loadLessons();
    await this.loadTests();
  },

  bindTabs() {
    document.querySelectorAll('[data-teacher-tab]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-teacher-tab]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.querySelectorAll('[data-teacher-panel]').forEach(p => {
          p.classList.toggle('d-none', p.dataset.teacherPanel !== btn.dataset.teacherTab);
        });
      });
    });
  },

  bindLessons() {
    document.getElementById('lessonForm')?.addEventListener('submit', e => {
      e.preventDefault();
      this.saveLesson();
    });
    document.getElementById('lessonCancelEdit')?.addEventListener('click', () => this.resetLessonForm());
    document.getElementById('lessonPreviewBtn')?.addEventListener('click', () => this.previewLesson());
    document.getElementById('lessonUnpublishBtn')?.addEventListener('click', () => this.unpublishLesson());
    document.getElementById('lessonImageFile')?.addEventListener('change', e => this.uploadLessonImage(e));
  },

  bindTests() {
    document.getElementById('testMetaForm')?.addEventListener('submit', e => {
      e.preventDefault();
      this.saveTestMeta();
    });
    document.getElementById('questionForm')?.addEventListener('submit', e => {
      e.preventDefault();
      this.addQuestion();
    });
    document.getElementById('testSelect')?.addEventListener('change', () => {
      const id = document.getElementById('testSelect').value;
      if (id) this.loadTestDetail(id);
      else this.hideTestEditor();
    });
    document.getElementById('newTestBtn')?.addEventListener('click', () => this.resetTestForm());
    document.getElementById('testPublishBtn')?.addEventListener('click', () => this.publishTest());
    document.getElementById('testUnpublishBtn')?.addEventListener('click', () => this.unpublishTest());
    document.getElementById('testDuplicateBtn')?.addEventListener('click', () => this.duplicateTest());
    document.getElementById('testImportBtn')?.addEventListener('click', () => this.importTest());
    document.getElementById('saveQuestionEditBtn')?.addEventListener('click', () => this.saveQuestionEdit());
  },

  bindClasses() {
    document.getElementById('createClassBtn')?.addEventListener('click', () => this.createClass());
    document.getElementById('enrollBtn')?.addEventListener('click', () => this.enrollStudent());
  },

  lessonPayload() {
    return {
      title_ru: document.getElementById('lessonTitleRu').value.trim(),
      title_tg: document.getElementById('lessonTitleTg').value.trim() || document.getElementById('lessonTitleRu').value.trim(),
      title_en: document.getElementById('lessonTitleEn').value.trim(),
      content_ru: document.getElementById('lessonContentRu').value.trim(),
      content_tg: document.getElementById('lessonContentTg').value.trim() || document.getElementById('lessonContentRu').value.trim(),
      content_en: document.getElementById('lessonContentEn').value.trim() || document.getElementById('lessonContentRu').value.trim(),
      category: document.getElementById('lessonCategory').value,
      order_index: parseInt(document.getElementById('lessonOrder').value, 10) || 0,
      image_urls: this.lessonImages,
    };
  },

  renderLessonImages() {
    const box = document.getElementById('lessonImages');
    if (!box) return;
    box.innerHTML = this.lessonImages
      .map(
        (url, i) => `<div class="position-relative">
        <img src="${url}" class="rounded" style="height:60px" alt="">
        <button type="button" class="btn btn-sm btn-danger position-absolute top-0 end-0" data-rm-img="${i}">×</button>
      </div>`
      )
      .join('');
    box.querySelectorAll('[data-rm-img]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.lessonImages.splice(parseInt(btn.dataset.rmImg, 10), 1);
        this.renderLessonImages();
      });
    });
  },

  async uploadLessonImage(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch('/api/teacher/upload/image', {
      method: 'POST',
      headers: { Authorization: `Bearer ${Auth.token}` },
      body: fd,
    });
    const data = await res.json();
    if (!res.ok) return alert(data.detail || 'Upload failed');
    this.lessonImages.push(data.url);
    this.renderLessonImages();
    e.target.value = '';
  },

  updateLessonPublishButtons(isPublished) {
    document.getElementById('lessonUnpublishBtn')?.classList.toggle('d-none', !isPublished || !this.editingLessonId);
    const chk = document.getElementById('lessonPublishNow');
    if (chk) chk.checked = !isPublished;
  },

  async previewLesson() {
    const box = document.getElementById('lessonPreviewBox');
    const content = document.getElementById('lessonPreviewContent');
    if (this.editingLessonId) {
      const l = await API.get(`/api/teacher/lessons/${this.editingLessonId}/preview`);
      this.showLessonPreview(l, content);
    } else {
      this.showLessonPreview(this.lessonPayload(), content);
    }
    box.classList.remove('d-none');
  },

  showLessonPreview(l, el) {
    const imgs = (l.image_urls || [])
      .map(u => `<img src="${u}" class="img-fluid rounded mb-2 me-2" style="max-height:120px">`)
      .join('');
    el.innerHTML = `
      <h4>${this.escape(I18n.field(l, 'title') || l.title_ru)}</h4>
      <div class="mb-2">${imgs}</div>
      <p>${this.escape(I18n.field(l, 'content') || l.content_ru).replace(/\n/g, '<br>')}</p>`;
  },

  async publishLesson() {
    if (!this.editingLessonId) return;
    const r = await API.post(`/api/teacher/lessons/${this.editingLessonId}/publish`, {});
    alert(`${I18n.t('teacher.published')} (${r.notified})`);
    await this.loadLessons();
  },

  async unpublishLesson() {
    if (!this.editingLessonId) return;
    await API.post(`/api/teacher/lessons/${this.editingLessonId}/unpublish`, {});
    await this.loadLessons();
  },

  async loadLessons() {
    const lessons = await API.get('/api/teacher/lessons');
    const list = document.getElementById('lessonsList');
    list.innerHTML = lessons.length
      ? lessons
          .map(
            l => `
      <div class="border-bottom py-2">
        <div class="d-flex justify-content-between align-items-start gap-2">
          <div>
            <strong>${this.escape(l.title_ru)}</strong>
            <span class="badge bg-secondary ms-1">${l.category}</span>
            ${l.is_published ? '<span class="badge bg-success ms-1">✓</span>' : '<span class="badge bg-warning ms-1">draft</span>'}
            <br><small class="text-muted">#${l.order_index}</small>
          </div>
          <div class="btn-group btn-group-sm">
            <button type="button" class="btn btn-outline-primary" data-edit-lesson="${l.id}">${I18n.t('teacher.edit')}</button>
            <button type="button" class="btn btn-outline-danger" data-del-lesson="${l.id}">×</button>
          </div>
        </div>
      </div>`
          )
          .join('')
      : `<p class="text-muted">${I18n.t('teacher.emptyLessons')}</p>`;

    list.querySelectorAll('[data-edit-lesson]').forEach(btn => {
      btn.addEventListener('click', () => this.editLesson(btn.dataset.editLesson, lessons));
    });
    list.querySelectorAll('[data-del-lesson]').forEach(btn => {
      btn.addEventListener('click', () => this.deleteLesson(btn.dataset.delLesson));
    });
  },

  editLesson(id, lessons) {
    const l = lessons.find(x => String(x.id) === String(id));
    if (!l) return;
    this.editingLessonId = l.id;
    document.getElementById('lessonTitleRu').value = l.title_ru;
    document.getElementById('lessonTitleTg').value = l.title_tg;
    document.getElementById('lessonTitleEn').value = l.title_en;
    document.getElementById('lessonContentRu').value = l.content_ru;
    document.getElementById('lessonContentTg').value = l.content_tg;
    document.getElementById('lessonContentEn').value = l.content_en;
    document.getElementById('lessonCategory').value = l.category;
    document.getElementById('lessonOrder').value = l.order_index;
    this.lessonImages = l.image_urls || [];
    this.renderLessonImages();
    document.getElementById('lessonFormTitle').textContent = I18n.t('teacher.editLesson');
    document.getElementById('lessonCancelEdit').classList.remove('d-none');
    this.updateLessonPublishButtons(l.is_published);
  },

  resetLessonForm() {
    this.editingLessonId = null;
    this.lessonImages = [];
    document.getElementById('lessonForm').reset();
    this.renderLessonImages();
    document.getElementById('lessonFormTitle').textContent = I18n.t('teacher.newLesson');
    document.getElementById('lessonCancelEdit').classList.add('d-none');
    document.getElementById('lessonPreviewBox')?.classList.add('d-none');
    this.updateLessonPublishButtons(false);
  },

  async saveLesson() {
    const payload = this.lessonPayload();
    if (!payload.title_ru || !payload.content_ru) {
      alert(I18n.t('teacher.fillRequired'));
      return;
    }
    if (this.editingLessonId) {
      await API.patch(`/api/teacher/lessons/${this.editingLessonId}`, payload);
    } else {
      const created = await API.post('/api/teacher/lessons', payload);
      this.editingLessonId = created.id;
      this.updateLessonPublishButtons(false);
    }
    let notified = 0;
    if (document.getElementById('lessonPublishNow')?.checked) {
      const pub = await API.post(`/api/teacher/lessons/${this.editingLessonId}/publish`, {});
      notified = pub.notified ?? 0;
    }
    await this.loadLessons();
    alert(
      document.getElementById('lessonPublishNow')?.checked
        ? `${I18n.t('teacher.published')} (${notified})`
        : I18n.t('teacher.savedDraft')
    );
  },

  async deleteLesson(id) {
    if (!confirm(I18n.t('teacher.confirmDelete'))) return;
    await API.delete(`/api/teacher/lessons/${id}`);
    await this.loadLessons();
  },

  async loadTests() {
    const tests = await API.get('/api/teacher/tests');
    const select = document.getElementById('testSelect');
    const classSelect = document.getElementById('testClassId');
    const opts = tests.map(t => `<option value="${t.id}">${this.escape(t.title_ru)} (${t.question_count} ${I18n.t('teacher.questions')})</option>`);
    select.innerHTML = `<option value="">${I18n.t('teacher.selectTest')}</option>` + opts.join('');

    document.getElementById('testsList').innerHTML = tests.length
      ? tests
          .map(
            t => `
      <div class="border-bottom py-2 d-flex justify-content-between align-items-center">
        <span><strong>${this.escape(t.title_ru)}</strong>
          ${t.is_published ? '<span class="badge bg-success">✓</span>' : '<span class="badge bg-warning">draft</span>'}
          — ${t.question_count} ${I18n.t('teacher.questions')}</span>
        <button type="button" class="btn btn-sm btn-outline-danger" data-del-test="${t.id}">×</button>
      </div>`
          )
          .join('')
      : `<p class="text-muted">${I18n.t('teacher.emptyTests')}</p>`;

    document.querySelectorAll('[data-del-test]').forEach(btn => {
      btn.addEventListener('click', async () => {
        if (!confirm(I18n.t('teacher.confirmDelete'))) return;
        await API.delete(`/api/teacher/tests/${btn.dataset.delTest}`);
        this.hideTestEditor();
        await this.loadTests();
      });
    });
  },

  resetTestForm() {
    this.currentTestId = null;
    document.getElementById('testMetaForm').reset();
    document.getElementById('testSelect').value = '';
    document.getElementById('testEditor').classList.add('d-none');
    document.getElementById('testMetaTitle').textContent = I18n.t('teacher.newTest');
    this.updateTestActionButtons(null);
  },

  hideTestEditor() {
    this.currentTestId = null;
    document.getElementById('testEditor').classList.add('d-none');
  },

  updateTestActionButtons(test) {
    const has = !!this.currentTestId;
    document.getElementById('testDuplicateBtn')?.classList.toggle('d-none', !has);
    document.getElementById('testPublishBtn')?.classList.toggle('d-none', !has || test?.is_published);
    document.getElementById('testUnpublishBtn')?.classList.toggle('d-none', !has || !test?.is_published);
  },

  async saveTestMeta() {
    const classVal = document.getElementById('testClassId').value;
    const payload = {
      title_ru: document.getElementById('testTitleRu').value.trim(),
      title_tg: document.getElementById('testTitleTg').value.trim(),
      title_en: document.getElementById('testTitleEn').value.trim(),
      description_ru: document.getElementById('testDescRu').value.trim(),
      category: document.getElementById('testCategory').value,
      class_id: classVal ? parseInt(classVal, 10) : null,
    };
    if (!payload.title_ru) {
      alert(I18n.t('teacher.fillRequired'));
      return;
    }
    let test;
    if (this.currentTestId) {
      test = await API.patch(`/api/teacher/tests/${this.currentTestId}`, payload);
    } else {
      test = await API.post('/api/teacher/tests', payload);
      this.currentTestId = test.id;
    }
    await this.loadTests();
    document.getElementById('testSelect').value = test.id;
    document.getElementById('testEditor').classList.remove('d-none');
    await this.loadTestDetail(test.id);
    alert(I18n.t('common.success'));
  },

  async loadTestDetail(id) {
    this.currentTestId = parseInt(id, 10);
    const test = await API.get(`/api/teacher/tests/${id}`);
    document.getElementById('testEditor').classList.remove('d-none');
    document.getElementById('testTitleRu').value = test.title_ru;
    document.getElementById('testTitleTg').value = test.title_tg;
    document.getElementById('testTitleEn').value = test.title_en;
    document.getElementById('testDescRu').value = test.description_ru;
    document.getElementById('testCategory').value = test.category;
    document.getElementById('testClassId').value = test.class_id || '';
    document.getElementById('testMetaTitle').textContent = I18n.t('teacher.editTest');
    this.currentTestQuestions = test.questions;
    this.updateTestActionButtons(test);
    this.fillEditQuestionSelect(test.questions);

    const qList = document.getElementById('questionsList');
    qList.innerHTML = test.questions.length
      ? test.questions
          .map(
            (q, i) => `
        <div class="border rounded p-2 mb-2">
          <div class="d-flex justify-content-between">
            <strong>${i + 1}. ${this.escape(q.question_ru)}</strong>
            <button type="button" class="btn btn-sm btn-outline-danger" data-del-q="${q.id}">×</button>
          </div>
          <ul class="small mb-0 mt-1">${q.options_ru.map((o, oi) => `<li${oi === q.correct_answer ? ' class="text-success fw-bold"' : ''}>${this.escape(o)}</li>`).join('')}</ul>
          <small class="text-muted">${q.points} ${I18n.t('teacher.points')}</small>
        </div>`
          )
          .join('')
      : `<p class="text-muted small">${I18n.t('teacher.noQuestions')}</p>`;

    qList.querySelectorAll('[data-del-q]').forEach(btn => {
      btn.addEventListener('click', async () => {
        await API.delete(`/api/teacher/tests/${id}/questions/${btn.dataset.delQ}`);
        await this.loadTestDetail(id);
        await this.loadTests();
      });
    });
  },

  getOptionsFromInputs() {
    return [...document.querySelectorAll('.q-option-input')]
      .map(inp => inp.value.trim())
      .filter(Boolean);
  },

  async addQuestion() {
    if (!this.currentTestId) {
      alert(I18n.t('teacher.saveTestFirst'));
      return;
    }
    const options = this.getOptionsFromInputs();
    if (options.length < 2) {
      alert(I18n.t('teacher.minOptions'));
      return;
    }
    const correct = parseInt(document.getElementById('qCorrect').value, 10);
    if (Number.isNaN(correct) || correct < 0 || correct >= options.length) {
      alert(I18n.t('teacher.invalidCorrect'));
      return;
    }
    await API.post(`/api/teacher/tests/${this.currentTestId}/questions`, {
      question_ru: document.getElementById('qTextRu').value.trim(),
      question_tg: document.getElementById('qTextTg').value.trim(),
      question_en: document.getElementById('qTextEn').value.trim(),
      options_ru: options,
      correct_answer: correct,
      points: parseInt(document.getElementById('qPoints').value, 10) || 10,
      hint_ru: document.getElementById('qHint').value.trim(),
    });
    document.getElementById('questionForm').reset();
    document.querySelectorAll('.q-option-input').forEach((inp, i) => {
      if (i < 4) inp.value = '';
    });
    await this.loadTestDetail(this.currentTestId);
    await this.loadTests();
    alert(I18n.t('common.success'));
  },

  fillEditQuestionSelect(questions) {
    const sel = document.getElementById('editQuestionSelect');
    if (!sel) return;
    sel.innerHTML = questions.map((q, i) => `<option value="${q.id}">${i + 1}. ${this.escape(q.question_ru)}</option>`).join('');
    sel.onchange = () => {
      const q = questions.find(x => String(x.id) === sel.value);
      if (!q) return;
      document.getElementById('editQTextRu').value = q.question_ru;
      document.getElementById('editQOptions').value = q.options_ru.join(' | ');
      document.getElementById('editQCorrect').value = q.correct_answer;
      document.getElementById('editQPoints').value = q.points;
    };
    if (questions[0]) sel.dispatchEvent(new Event('change'));
  },

  async saveQuestionEdit() {
    const qid = document.getElementById('editQuestionSelect').value;
    if (!qid || !this.currentTestId) return;
    const options = document.getElementById('editQOptions').value.split('|').map(s => s.trim()).filter(Boolean);
    await API.patch(`/api/teacher/tests/${this.currentTestId}/questions/${qid}`, {
      question_ru: document.getElementById('editQTextRu').value.trim(),
      options_ru: options,
      correct_answer: parseInt(document.getElementById('editQCorrect').value, 10),
      points: parseInt(document.getElementById('editQPoints').value, 10) || 10,
    });
    await this.loadTestDetail(this.currentTestId);
    alert(I18n.t('common.success'));
  },

  async publishTest() {
    if (!this.currentTestId) return;
    const r = await API.post(`/api/teacher/tests/${this.currentTestId}/publish`, {});
    alert(`${I18n.t('teacher.published')} (${r.notified})`);
    await this.loadTestDetail(this.currentTestId);
    await this.loadTests();
  },

  async unpublishTest() {
    if (!this.currentTestId) return;
    await API.post(`/api/teacher/tests/${this.currentTestId}/unpublish`, {});
    await this.loadTestDetail(this.currentTestId);
    await this.loadTests();
  },

  async duplicateTest() {
    if (!this.currentTestId) return;
    const t = await API.post(`/api/teacher/tests/${this.currentTestId}/duplicate`, {});
    await this.loadTests();
    document.getElementById('testSelect').value = t.id;
    await this.loadTestDetail(t.id);
  },

  async importTest() {
    try {
      const data = JSON.parse(document.getElementById('testImportJson').value);
      const t = await API.post('/api/teacher/tests/import', data);
      await this.loadTests();
      document.getElementById('testSelect').value = t.id;
      await this.loadTestDetail(t.id);
      alert(I18n.t('common.success'));
    } catch (e) {
      alert(e.message || 'Invalid JSON');
    }
  },

  async loadClasses() {
    const list = await API.get('/api/teacher/classes');
    const classSelect = document.getElementById('testClassId');
    if (classSelect) {
      classSelect.innerHTML =
        `<option value="">— ${I18n.t('teacher.allStudents')} —</option>` +
        list.map(c => `<option value="${c.id}">${this.escape(c.name)} (ID ${c.id})</option>`).join('');
    }
    document.getElementById('classesList').innerHTML = list.length
      ? list
          .map(
            c => `
      <div class="border-bottom py-2 d-flex justify-content-between align-items-center">
        <span><strong>${this.escape(c.name)}</strong> <small class="text-muted">ID: ${c.id}</small> — ${c.student_count} ${I18n.t('teacher.students')}</span>
        <button type="button" class="btn btn-sm btn-outline-secondary" data-class-progress="${c.id}">${I18n.t('teacher.progress')}</button>
      </div>`
          )
          .join('')
      : `<p class="text-muted">—</p>`;

    document.querySelectorAll('[data-class-progress]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const p = await API.get(`/api/teacher/classes/${btn.dataset.classProgress}/progress`);
        document.getElementById('classProgress').innerHTML = `
          <h6 class="mt-3">${this.escape(p.name)}</h6>
          <table class="table table-sm">
            <thead><tr><th>${I18n.t('login.username')}</th><th>${I18n.t('teacher.testsTaken')}</th><th>%</th></tr></thead>
            <tbody>${p.students.map(s => `<tr><td>${this.escape(s.username)}</td><td>${s.tests_taken}</td><td>${s.avg_percentage}</td></tr>`).join('') || `<tr><td colspan="3">—</td></tr>`}</tbody>
          </table>`;
      });
    });
  },

  async createClass() {
    const name = document.getElementById('className').value.trim();
    if (!name) return;
    await API.post('/api/teacher/classes', { name });
    document.getElementById('className').value = '';
    await this.loadClasses();
  },

  async enrollStudent() {
    const classId = document.getElementById('enrollClassId').value;
    const username = document.getElementById('enrollUsername').value.trim();
    await API.post(`/api/teacher/classes/${classId}/enroll`, { username });
    await this.loadClasses();
    alert(I18n.t('common.success'));
  },

  escape(s) {
    const d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
  },
};

document.addEventListener('DOMContentLoaded', () => Teacher.init());
