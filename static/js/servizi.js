function apriPopupNuovoServizio() {
  const p = document.getElementById('popup-nuovo-servizio');
  p.classList.remove('hidden');
  p.classList.add('visibile');
}

function chiudiPopupNuovoServizio() {
  const p = document.getElementById('popup-nuovo-servizio');
  p.classList.remove('visibile');
  p.classList.add('hidden');
}

function creaServizio() {
  const form = document.getElementById('form-nuovo-servizio');
  const data = new FormData(form);
  fetch('/admin/servizi/crea', {
    method: 'POST',
    body: data
  }).then(r => {
    if (r.ok) {
      chiudiPopupNuovoServizio();
      location.reload();
    } else {
      alert('Errore creazione servizio');
    }
  });
}

function apriPopupServizio(servizio) {
  document.getElementById('servizio-id').value = servizio.id;
  document.getElementById('servizio-nome').value = servizio.nome || '';
  document.getElementById('servizio-descrizione').value = servizio.descrizione || '';
  document.getElementById('servizio-immagine').value = servizio.immagine || '';
  document.getElementById('servizio-costo').value = servizio.costo || '';
  document.getElementById('servizio-durata').value = servizio.durata || '';
  const p = document.getElementById('popup-servizio');
  p.classList.remove('hidden');
  p.classList.add('visibile');
}

function chiudiPopupServizio() {
  const p = document.getElementById('popup-servizio');
  p.classList.remove('visibile');
  p.classList.add('hidden');
}

function salvaServizio() {
  const form = document.getElementById('form-servizio');
  const data = new FormData(form);
  fetch('/admin/servizi/update', {
    method: 'POST',
    body: data
  }).then(r => {
    if (r.ok) {
      chiudiPopupServizio();
      location.reload();
    } else {
      alert('Errore salvataggio');
    }
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
    if (r.ok) {
      chiudiPopupServizio();
      location.reload();
    } else {
      alert('Errore eliminazione');
    }
  });
}

let campoImmagineCorrente = null;

function apriSelezionaImmagine(inputId) {
  campoImmagineCorrente = inputId;
  fetch('/admin/servizi/immagini')
    .then(r => r.json())
    .then(urls => {
      const cont = document.getElementById('lista-immagini-servizi');
      cont.innerHTML = '';
      urls.forEach(u => {
        const img = document.createElement('img');
        img.src = u;
        img.style.width = '100px';
        img.style.cursor = 'pointer';
        img.onclick = () => selezionaImmagineServizio(u);
        cont.appendChild(img);
      });
      document.getElementById('popup-seleziona-immagine').classList.remove('hidden');
    });
}

function selezionaImmagineServizio(url) {
  if (campoImmagineCorrente) {
    document.getElementById(campoImmagineCorrente).value = url;
  }
  chiudiSelezionaImmagine();
}

function chiudiSelezionaImmagine() {
  document.getElementById('popup-seleziona-immagine').classList.add('hidden');
}

