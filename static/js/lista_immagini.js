
function apriPopupImmagine(id, nome, url) {
  document.getElementById("popup-img-id").value = id;
  document.getElementById("popup-img-nome").value = nome || "";
  document.getElementById("popup-img-download").href = url;
  document.getElementById("form-elimina-img").action =
    `/admin/immagini/elimina/${id}`;
  document.getElementById("popup-immagine").classList.add("visibile");
}

function chiudiPopupImmagine() {
  document.getElementById("popup-immagine").classList.remove("visibile");
}

function salvaNomeImmagine() {
  const id = document.getElementById("popup-img-id").value;
  const nome = document.getElementById("popup-img-nome").value;
  fetch("/admin/immagini/update_nome", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `id=${encodeURIComponent(id)}&nome=${encodeURIComponent(nome)}`
  }).then(res => res.json())
    .then(data => {
      if (data.success) {
        alert("Nome aggiornato!");
        chiudiPopupImmagine();
        location.reload();
      } else {
        alert("Errore nel salvataggio");
      }
    });
}

function confermaElimina() {
  return confirm("Vuoi davvero eliminare questa immagine?");
}

