document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('nuovo-appuntamento');
  if (!form) return;
  const carrello = [];
  const carrelloEl = document.getElementById('carrello');
  const slotSection = document.getElementById('seleziona-slot');

  document.querySelectorAll('.add-servizio').forEach((btn) => {
    btn.addEventListener('click', () => {
      carrello.push({ id: btn.dataset.id, nome: btn.dataset.nome });
      const li = document.createElement('li');
      li.textContent = btn.dataset.nome;
      carrelloEl.appendChild(li);
      slotSection.classList.remove('hidden');
    });
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!carrello.length) {
      alert('Seleziona almeno un servizio');
      return;
    }
    const data = {
      freelancer_id: form.freelancer_id.value,
      cliente_id: form.cliente_id.value,
      data_ora: form.data_ora.value,
      servizi: carrello.map((s) => s.id),
    };
    const res = await fetch('/appuntamenti', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (res.ok) {
      alert('Richiesta inviata');
      location.reload();
    } else {
      alert('Errore invio richiesta');
    }
  });
});
