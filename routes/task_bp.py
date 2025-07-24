from flask import Blueprint, request, jsonify # type: ignore
from PIL import Image, UnidentifiedImageError # type: ignore
from io import BytesIO
from google.cloud import storage, firestore

task_bp = Blueprint("task", __name__, url_prefix="/task")

@task_bp.route("/elabora-immagine", methods=["POST"])
def elabora_immagine():
    try:
        data = request.get_json()
        foto_id = data.get("foto_id")
        filename = data.get("filename")
        cliente_id = data.get("cliente_id")

        if not foto_id or not filename or not cliente_id:
            print("❌ Task ricevuto senza foto_id, filename, o cliente_id")
            return jsonify({"error": "Dati mancanti"}), 400

        print(f"📥 Task ricevuto: {cliente_id} - {foto_id} - {filename}")

        # Get client config from central DB
        central_db = firestore.Client()
        query = central_db.collection("clienti_config").where("cliente_id", "==", cliente_id).limit(1).get()
        if not query:
            return jsonify({"error": "Cliente non trovato"}), 404

        client_config = query[0].to_dict()
        firestore_db_id = client_config.get("firestore_db_id")
        bucket_name = client_config.get("bucket_name")

        if not firestore_db_id or not bucket_name:
            return jsonify({"error": "Database cliente non configurato"}), 500

        # Initialize tenant-specific clients
        db = firestore.Client(database=firestore_db_id)
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        # Download original image
        blob_path = f"foto/originals/{filename}"
        original_blob = bucket.blob(blob_path)

        if not original_blob.exists():
            print(f"❌ File non trovato su GCS: {blob_path}")
            return jsonify({"error": "File non trovato"}), 404

        original_data = original_blob.download_as_bytes()

        try:
            image = Image.open(BytesIO(original_data)).convert("RGB")
        except UnidentifiedImageError as e:
            print(f"❌ Immagine non valida: {filename} – {e}")
            return jsonify({"error": "Immagine non valida"}), 400

        # Create versions
        thumb = resize_image(image, 300)
        web = resize_image(image, 1200)

        # Upload to GCS
        thumb_path = f"foto/thumb/{filename}"
        web_path = f"foto/web/{filename}"

        bucket.blob(thumb_path).upload_from_file(thumb, content_type="image/jpeg")
        bucket.blob(web_path).upload_from_file(web, content_type="image/jpeg")

        print(f"📤 Versioni caricate: {thumb_path}, {web_path}")

        # Public links
        base_url = f"https://storage.googleapis.com/{bucket_name}"
        links = {
            "original": f"{base_url}/{blob_path}",
            "web": f"{base_url}/{web_path}",
            "thumb": f"{base_url}/{thumb_path}",
        }

        # Save to Firestore
        db.collection("foto_pubbliche").document(foto_id).set({
            **links,
            "timestamp": firestore.SERVER_TIMESTAMP
        }, merge=True)

        print(f"✅ Firestore aggiornato per {foto_id}")
        return jsonify({"success": True})

    except Exception as e:
        print("❌ Errore nel task /elabora-immagine:", e)
        return jsonify({"error": "Errore interno"}), 500


def resize_image(image, max_size):
    ratio = max_size / max(image.size)
    new_size = tuple(int(x * ratio) for x in image.size)
    resized = image.resize(new_size, Image.LANCZOS)
    buffer = BytesIO()
    resized.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)
    return buffer
