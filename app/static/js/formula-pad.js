const FormulaPad = {
  init(inputId, containerId = 'formulaPad') {
    const input = document.getElementById(inputId);
    const container = document.getElementById(containerId);
    if (!input || !container) return;

    const buttons = [
      'x', '**2', '**3', 'sin(', 'cos(', 'tan(', 'exp(', 'log(', 'sqrt(',
      'pi', '+', '-', '*', '/', '(', ')', '^',
    ];

    container.innerHTML = buttons
      .map(
        b =>
          `<button type="button" class="btn btn-sm btn-outline-secondary formula-pad-btn" data-insert="${b}">${b.replace('**2', '²').replace('**3', '³')}</button>`
      )
      .join('');

    container.querySelectorAll('.formula-pad-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const ins = btn.dataset.insert;
        const start = input.selectionStart ?? input.value.length;
        const end = input.selectionEnd ?? input.value.length;
        input.value = input.value.slice(0, start) + ins + input.value.slice(end);
        input.focus();
      });
    });
  },
};

window.FormulaPad = FormulaPad;
