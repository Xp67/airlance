let allImages = [];

// Fetch all images once on page load
fetch("/admin/immagini/tutte")
    .then(response => response.json())
    .then(data => {
        allImages = data;
    });

function openCollectionPopup(imageIds, collectionName) {
    const popup = document.getElementById('collection-popup');
    const imagesGrid = document.getElementById('popup-images-grid');
    const collectionNameEl = document.getElementById('popup-collection-name');

    imagesGrid.innerHTML = '';
    collectionNameEl.textContent = collectionName;

    const imagesToShow = allImages.filter(img => imageIds.includes(img.id));

    imagesToShow.forEach(image => {
        const portfolioItem = document.createElement('div');
        portfolioItem.className = 'portfolio-item';
        const img = document.createElement('img');
        img.src = image.web || image.thumb || image.original;
        portfolioItem.appendChild(img);
        imagesGrid.appendChild(portfolioItem);
    });

    popup.classList.remove('hidden');
    popup.classList.add('visibile');
}

function closeCollectionPopup() {
    const popup = document.getElementById('collection-popup');
    popup.classList.remove('visibile');
    popup.classList.add('hidden');
}
