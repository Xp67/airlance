function apriPopupNuovoServizio() {
  const p = document.getElementById('popup-nuovo-servizio');
  document.getElementById('form-nuovo-servizio').reset();
  document.getElementById('nuovo-immagine').value = '';
  document.getElementById('nuovo-immagine-preview').src = '/static/img/placeholder.jpg';
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
  convertAndSubmit(form, '/admin/servizi/crea');
}

function apriPopupServizio(servizio) {
  document.getElementById('servizio-id').value = servizio.id;
  document.getElementById('servizio-nome').value = servizio.nome || '';
  document.getElementById('servizio-descrizione').value = servizio.descrizione || '';
  document.getElementById('servizio-immagine').value = servizio.immagine || '';
  document.getElementById('servizio-immagine-preview').src = servizio.immagine || '/static/img/placeholder.jpg';
  document.getElementById('servizio-immagine-file').value = '';
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
  convertAndSubmit(form, '/admin/servizi/update');
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

function apriSelezionaImmagine(inputId, previewId) {
  campoImmagineCorrente = { inputId, previewId };
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
    document.getElementById(campoImmagineCorrente.inputId).value = url;
    if (campoImmagineCorrente.previewId) {
      document.getElementById(campoImmagineCorrente.previewId).src = url;
    }
  }
  chiudiSelezionaImmagine();
}

function chiudiSelezionaImmagine() {
  document.getElementById('popup-seleziona-immagine').classList.add('hidden');
}

function anteprimaFile(input, previewId, hiddenId) {
  const file = input.files && input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    document.getElementById(previewId).src = e.target.result;
  };
  reader.readAsDataURL(file);
  if (hiddenId) {
    document.getElementById(hiddenId).value = '';
  }
}

async function convertImageToJpeg(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        canvas.toBlob((blob) => {
          if (blob) {
            const newFile = new File([blob], file.name.replace(/\.[^/.]+$/, ".jpeg"), {
              type: 'image/jpeg',
              lastModified: Date.now()
            });
            resolve(newFile);
          } else {
            reject(new Error('Canvas to Blob conversion failed'));
          }
        }, 'image/jpeg', 0.95);
      };
      img.onerror = reject;
      img.src = event.target.result;
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function convertAndSubmit(form, url) {
  const formData = new FormData(form);
  const fileInput = form.querySelector('input[type="file"]');
  const file = fileInput.files[0];

  if (file) {
    const allowedExtensions = ['jpg', 'jpeg', 'png'];
    const fileExtension = file.name.split('.').pop().toLowerCase();

    if (!allowedExtensions.includes(fileExtension)) {
      try {
        const convertedFile = await convertImageToJpeg(file);
        formData.set(fileInput.name, convertedFile);
      } catch (error) {
        console.error('Error converting image:', error);
        alert('Errore durante la conversione dell\'immagine.');
        return;
      }
    }
  }

  fetch(url, {
    method: 'POST',
    body: formData
  }).then(r => {
    if (r.ok) {
      location.reload();
    } else {
      alert('Errore durante il salvataggio.');
    }
  });
}
