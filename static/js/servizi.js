function apriPopupNuovoServizio() {
  document.getElementById('popup-nuovo-servizio').classList.remove('hidden');
}

function chiudiPopupNuovoServizio() {
  document.getElementById('popup-nuovo-servizio').classList.add('hidden');
}

function creaServizio() {
  const data = {
    nome: document.getElementById('nuovo-nome').value,
    descrizione: document.getElementById('nuovo-descrizione').value,
    immagine: document.getElementById('nuovo-immagine').value,
    costo: document.getElementById('nuovo-costo').value,
    durata: document.getElementById('nuovo-durata').value
  };
  fetch('/admin/servizi/crea', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).then(r => {
    if (r.ok) location.reload();
    else alert('Errore creazione servizio');
  });
}

function apriPopupServizio(servizio) {
  document.getElementById('servizio-id').value = servizio.id;
  document.getElementById('servizio-nome').value = servizio.nome || '';
  document.getElementById('servizio-descrizione').value = servizio.descrizione || '';
  document.getElementById('servizio-immagine').value = servizio.immagine || '';
  document.getElementById('servizio-costo').value = servizio.costo || '';
  document.getElementById('servizio-durata').value = servizio.durata || '';
  document.getElementById('popup-servizio').classList.remove('hidden');
}

function chiudiPopupServizio() {
  document.getElementById('popup-servizio').classList.add('hidden');
}

function salvaServizio() {
  const data = {
    id: document.getElementById('servizio-id').value,
    nome: document.getElementById('servizio-nome').value,
    descrizione: document.getElementById('servizio-descrizione').value,
    immagine: document.getElementById('servizio-immagine').value,
    costo: document.getElementById('servizio-costo').value,
    durata: document.getElementById('servizio-durata').value
  };
  fetch('/admin/servizi/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).then(r => {
    if (r.ok) location.reload();
    else alert('Errore salvataggio');
  });
}

function eliminaServizio() {
  const id = document.getElementById('servizio-id').value;
  if (!confirm('Eliminare il servizio?')) return;
  fetch('/admin/servizi/elimina', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id })
  }).then(r => {
    if (r.ok) location.reload();
    else alert('Errore eliminazione');
  });
}

