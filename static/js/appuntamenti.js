document.addEventListener('DOMContentLoaded', () => {
  const carrello = [];
  const carrelloEl = document.getElementById('carrello');
  const carrelloContainer = document.getElementById('carrello-container');
  const procediBtn = document.getElementById('procedi-richiesta');

  document.querySelectorAll('.add-servizio').forEach((btn) => {
    btn.addEventListener('click', () => {
      carrello.push({ id: btn.dataset.id, nome: btn.dataset.nome });

      const li = document.createElement('li');
      li.dataset.id = btn.dataset.id;
      li.innerHTML = `<span>${btn.dataset.nome}</span><button type="button" class="remove-item">&times;</button>`;
      carrelloEl.appendChild(li);

      li.querySelector('.remove-item').addEventListener('click', () => {
        const index = carrello.findIndex((s) => s.id === li.dataset.id);
        if (index !== -1) carrello.splice(index, 1);
        li.remove();
        if (!carrello.length) {
          carrelloContainer.classList.remove('mostra');
        }
      });

      carrelloContainer.classList.add('mostra');
    });
  });

  if (procediBtn) {
    procediBtn.addEventListener('click', () => {
      alert('Funzione non ancora implementata');
    });
  }
});

