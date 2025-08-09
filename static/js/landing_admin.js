let currentCard = null;

function openImageSelector(index) {
  currentCard = index;
  fetch('/admin/landing/immagini')
    .then(r => r.json())
    .then(images => {
      const container = document.getElementById('lista-immagini-landing');
      container.innerHTML = '';
      images.forEach(imgData => {
        const img = document.createElement('img');
        img.src = imgData.thumb;
        img.style.cursor = 'pointer';
        img.onclick = () => selectImage(imgData.web);
        container.appendChild(img);
      });
      const popup = document.getElementById('popup-seleziona-landing');
      popup.classList.remove('hidden');
      popup.classList.add('visibile');
    });
}

function selectImage(url) {
  if (currentCard !== null) {
    const imgEl = document.querySelector(`#card-${currentCard} img`);
    const inputEl = document.getElementById(`image${currentCard + 1}`);
    if (imgEl) imgEl.src = url;
    if (inputEl) inputEl.value = url;
  }
  closeImageSelector();
}

function closeImageSelector() {
  const popup = document.getElementById('popup-seleziona-landing');
  popup.classList.remove('visibile');
  popup.classList.add('hidden');
}
