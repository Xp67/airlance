// Inizializza il box in basso a destra
function inizializzaUploadBox() {
  let box = document.getElementById("upload-status-box");

  if (!box) {
    box = document.createElement("div");
    box.id = "upload-status-box";
    const title = document.createElement("strong");
    title.innerText = "Upload in corso";
    box.appendChild(title);

    const lista = document.createElement("div");
    lista.id = "upload-list";
    box.appendChild(lista);

    document.body.appendChild(box);
  }

  box.style.display = "block"; 
}

function aggiornaUploadItem(nome, stato) {
  const safeId = "upload-item-" + btoa(nome).replace(/=/g, "");
  let item = document.getElementById(safeId);
  if (!item) {
    item = document.createElement("div");
    item.id = safeId;
    document.getElementById("upload-list").appendChild(item);
  }
  item.textContent = `${nome}: ${stato}`;
}

function rimuoviUploadItem(nome) {
  const safeId = "upload-item-" + btoa(nome).replace(/=/g, "");
  const item = document.getElementById(safeId);
  if (item) item.remove();
  controllaBoxUpload(); 
}

async function uploadFotoFetch(inputId) {
  inizializzaUploadBox();

  const input = document.getElementById(inputId);
  if (!input || !input.files.length) return;

  const files = Array.from(input.files);

  for (const file of files) {
    const ext = file.name.split(".").pop();
    const foto_id_base = file.name.replace(/\.[^/.]+$/, "");
    const filename = `${foto_id_base}_${Date.now()}.${ext}`;
    const foto_id = filename.replace(/\.[^/.]+$/, "");

    aggiornaUploadItem(filename, "🔐 Genero URL...");

    try {
      const cliente_id = document.body.dataset.clienteId;

        // 🔐 Richiesta URL firmato
        const res = await fetch("/admin/signed-upload-url", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            filename,
            content_type: file.type,
            cliente_id: cliente_id,
        }),
        });

        if (!res.ok) throw new Error("Errore generazione signed URL");

        const { url, public_url } = await res.json();
        aggiornaUploadItem(filename, "📤 Upload in corso...");

        const xhr = new XMLHttpRequest();
        xhr.open("PUT", url, true);
        xhr.setRequestHeader("Content-Type", file.type || "application/octet-stream");

        xhr.upload.onprogress = function (e) {
        if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total) * 100);
            aggiornaUploadItem(filename, `📤 ${percent}%`);
        }
        };

        const uploadPromise = new Promise((resolve, reject) => {
        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
            resolve();
            } else {
            reject(new Error("Upload fallito con status " + xhr.status));
            }
        };
        xhr.onerror = () => {
            reject(new Error("Errore durante l'upload"));
        };
        });

        xhr.send(file);
        await uploadPromise;

        aggiornaUploadItem(filename, "⚙️ Invio a postprocess...");
        const postRes = await fetch("/admin/postprocess", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            filename,
            public_url,
            foto_id,
            cliente_id,
        }),
        });

        if (!postRes.ok) throw new Error("Errore postprocess");

        aggiornaUploadItem(filename, "✅ Completato");
        setTimeout(() => rimuoviUploadItem(filename), 3000);
    } catch (err) {
      console.error(err);
      aggiornaUploadItem(filename, "❌ Errore");
    }
  }

  input.value = "";
}

function controllaBoxUpload() {
  const lista = document.getElementById("upload-list");
  const box = document.getElementById("upload-status-box");
  if (lista && lista.children.length === 0 && box) {
    box.style.display = "none";
  }
}