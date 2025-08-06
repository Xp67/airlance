function apriPopup(nomeRaccolta) {
  fetch(`/admin/raccolte/dettaglio/${nomeRaccolta}`)
    .then(res => res.json())
    .then(data => {
      document.getElementById("popup-raccolta").classList.remove("hidden");
      document.getElementById("copertina-popup").src = data.copertina || "/static/img/placeholder.jpg";
      document.getElementById("nome-popup").value = data.nome;
      document.getElementById("id-popup").value = nomeRaccolta;
      document.getElementById("descrizione-popup").value = data.descrizione || "";

      // salva immagini della raccolta
      immaginiSelezionate = [...data.immagini.map(i => i.id)];

      // carica tutte le immagini
      fetch("/admin/immagini/tutte")
        .then(r => r.json())
        .then(tutte => {
          immaginiDisponibili = tutte;
          const container = document.getElementById("immagini-popup");
            container.innerHTML = "";

            data.immagini.forEach(img => {
            const div = document.createElement("div");
            div.classList.add("immagine-container");
            div.innerHTML = `
            <div class="img-wrapper" data-id="${img.id}">
                <img src="${img.thumb}" style="width: 100px; border-radius: 6px;">
                <button class="rimuovi-img-btn" onclick="rimuoviImmagineDaRaccolta('${img.id}')">✕</button>
            </div>`;
            container.appendChild(div);
            });

        });
    });

}


function chiudiPopup() {
  document.getElementById("popup-raccolta").classList.add("hidden");
}

let immaginiDisponibili = [];
let immaginiSelezionate = [];

function apriPopupCreazione() {
  const popup = document.getElementById("popup-nuova-raccolta");
  popup.classList.add("visibile");
  popup.classList.remove("hidden");

  console.log("Popup nuova raccolta aperto");
  const triggerBtn = document.querySelector(".nuova-raccolta-btn");
  if (triggerBtn) {
    const originalText = triggerBtn.textContent;
    triggerBtn.textContent = "Caricamento...";
    setTimeout(() => {
      triggerBtn.textContent = originalText;
    }, 1000);
  }

  immaginiSelezionate = [];
  document.getElementById("preview-immagini-scelte").innerHTML = "";
}

function chiudiPopupCreazione() {
  document.getElementById("popup-nuova-raccolta").classList.add("hidden");
}

function apriPopupSelezione() {
  fetch('/admin/immagini/tutte')
    .then(res => {
      if (!res.ok) {
        throw new Error(`Errore HTTP ${res.status}`);
      }
      return res.json();
    })
    .then(data => {
      if (!Array.isArray(data)) {
        console.error("Risposta inattesa dal server:", data);
        throw new Error("Formato dati non valido");
      }
      immaginiDisponibili = data;
      const container = document.getElementById("tutte-le-immagini");
      container.innerHTML = "";
      data.forEach(img => {
        const div = document.createElement("div");
        div.innerHTML = `
          <label style="display: block; text-align: center;">
            <img src="${img.thumb}" style="width: 100px; border-radius: 6px;"><br>
            <input type="checkbox" value="${img.id}" ${immaginiSelezionate.includes(img.id) ? "checked" : ""}>
          </label>`;
        container.appendChild(div);
      });

      document.getElementById("popup-selezione-immagini").classList.remove("hidden");
    })
    .catch(err => {
      console.error("Errore nel caricamento delle immagini:", err);
      alert(`Errore nel caricamento delle immagini: ${err.message}`);
    });
}


function chiudiPopupSelezione() {
  document.getElementById("popup-selezione-immagini").classList.add("hidden");
}

function confermaSelezioneImmagini() {
  const inputs = document.querySelectorAll("#tutte-le-immagini input[type='checkbox']");
  immaginiSelezionate = Array.from(inputs)
    .filter(i => i.checked)
    .map(i => i.value);

  const preview = document.getElementById("preview-immagini-scelte");
  preview.innerHTML = "";
  immaginiDisponibili.forEach(img => {
    if (immaginiSelezionate.includes(img.id)) {
      const i = document.createElement("img");
      i.src = img.thumb;
      preview.appendChild(i);
    }
  });

  chiudiPopupSelezione();
}

function salvaNuovaRaccolta() {
  const nome = document.getElementById("nome-nuovo").value.trim();
  const descrizione = document.getElementById("descrizione-nuovo").value.trim();
    console.log("→ nome:", nome);
    console.log("→ immagini:", immaginiSelezionate);
  if (!nome || immaginiSelezionate.length === 0) {
    alert("Devi inserire un nome e selezionare almeno un'immagine.");
    return;
  }

  fetch("/admin/raccolte/crea", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nome, descrizione, immagini: immaginiSelezionate })
  })
    .then(res => {
      if (res.ok) {
        location.reload(); // ricarica per vedere la nuova raccolta
      } else {
        res.text().then(msg => {
          alert(`Errore nella creazione della raccolta: ${msg}`);
        });
      }
    })
    .catch(err => {
      console.error("Errore creazione raccolta", err);
      alert(`Errore creazione raccolta: ${err.message}`);
    });
}

function salvaModificheRaccolta() {
  const id = document.getElementById("id-popup").value;
  const nome = document.getElementById("nome-popup").value.trim();
  const descrizione = document.getElementById("descrizione-popup").value;
  const fileInput = document.getElementById("nuova-copertina");
  const file = fileInput ? fileInput.files[0] : null;

  const formData = new FormData();
  formData.append("id", id);
  formData.append("nome", nome);
  formData.append("descrizione", descrizione);
  immaginiSelezionate.forEach(imgId => formData.append("immagini[]", imgId));
  if (file) {
    formData.append("copertina", file);
  }

  fetch("/admin/raccolte/update", {
    method: "POST",
    body: formData
  }).then(res => {
    if (res.ok) {
      location.reload();
    } else {
      alert("Errore nel salvataggio.");
    }
  });
}


function eliminaRaccolta() {
  const id = document.getElementById("id-popup").value;
  if (!confirm(`Vuoi davvero eliminare la raccolta "${id}"?`)) return;

  fetch("/admin/raccolte/elimina", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id })
  }).then(res => {
    if (res.ok) {
      location.reload();
    } else {
      alert("Errore nell'eliminazione.");
    }
  });
}

function apriPopupSelezioneModifica() {
  const container = document.getElementById("tutte-le-immagini-modifica");
  container.innerHTML = "";

  fetch("/admin/immagini/tutte")
    .then(r => r.json())
    .then(tutte => {
      const immaginiGiaPresenti = immaginiSelezionate; // già definite da apriPopup

      tutte.forEach(img => {
      if (immaginiGiaPresenti.includes(img.id)) return; // 🔴 salta se già presente

      const div = document.createElement("div");
      div.innerHTML = `
         <label style="display: block; text-align: center;">
         <img src="${img.thumb}" style="width: 100px; border-radius: 6px;"><br>
         <input type="checkbox" value="${img.id}">
         </label>`;
      container.appendChild(div);
});


      document.getElementById("popup-selezione-immagini-modifica").classList.remove("hidden");
    });
}

function chiudiPopupSelezioneModifica() {
  document.getElementById("popup-selezione-immagini-modifica").classList.add("hidden");
}

function confermaSelezioneImmaginiModifica() {
  const checks = document.querySelectorAll("#tutte-le-immagini-modifica input[type='checkbox']");
  const selezionate = Array.from(checks).filter(i => i.checked).map(i => i.value);

  const container = document.getElementById("immagini-popup");

  selezionate.forEach(id => {
  if (!immaginiSelezionate.includes(id)) {
    immaginiSelezionate.push(id); // 🔁 aggiorna lista per il salvataggio

    const thumb = immaginiDisponibili.find(i => i.id === id)?.thumb;
    const div = document.createElement("div");
    div.classList.add("immagine-container");
    div.innerHTML = `
      <div class="img-wrapper" data-id="${id}">
        <img src="${thumb}" style="width: 100px; border-radius: 6px;" data-id="${id}">
        <button class="rimuovi-img-btn" onclick="rimuoviImmagineDaRaccolta('${id}')">✕</button>
      </div>`;
    container.appendChild(div);
  }
});


  chiudiPopupSelezioneModifica();
}

function rimuoviImmagineDaRaccolta(id) {
  immaginiSelezionate = immaginiSelezionate.filter(i => i !== id);
  const wrapper = document.querySelector(`.img-wrapper[data-id="${id}"]`);
  if (wrapper) wrapper.remove();
}


document.getElementById('nuova-raccolta-btn')
  .addEventListener('click', apriPopupCreazione);

