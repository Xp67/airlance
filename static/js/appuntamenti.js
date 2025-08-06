document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('nuovo-appuntamento');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
      freelancer_id: form.freelancer_id.value,
      cliente_id: form.cliente_id.value,
      data_ora: form.data_ora.value,
      stato: form.stato.value,
    };
    const res = await fetch('/appuntamenti', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (res.ok) {
      location.reload();
    } else {
      alert('Errore creazione appuntamento');
    }
  });
});
