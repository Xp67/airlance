from flask import Blueprint, redirect, request, session, url_for, render_template, flash, jsonify, g  # type: ignore
from werkzeug.utils import secure_filename  # type: ignore
from google.cloud import firestore, tasks_v2, storage
from datetime import datetime
import json
import os
from services.storage import firma_url
from services.decorators import admin_required
import re
import unicodedata
from services.image_utils import process_image
import logging







admin_bp = Blueprint('admin', __name__,url_prefix='/admin')
logger = logging.getLogger(__name__)


def clean_servizio_id(nome: str) -> str:
    """Return a Firestore-safe document ID derived from the given name."""
    # Normalize to ASCII and remove disallowed characters
    normale = unicodedata.normalize('NFD', nome)
    ascii_only = normale.encode('ascii', 'ignore').decode('ascii')
    base = ascii_only.lower().replace(' ', '_')
    return re.sub(r'[^a-z0-9_]+', '', base)


@admin_bp.route("/admin_dashboard")
@admin_required
def admin_dashboard():
    return render_template("admin.html")

@admin_bp.route('/carica-immagini')
@admin_required
def carica_immagini():
    # g.db è già configurato per puntare al Firestore del tenant corrente
    foto_ref = g.db.collection("foto_pubbliche") \
        .order_by("timestamp", direction=firestore.Query.DESCENDING) \
        .limit(10)
    
    docs = foto_ref.stream()

    immagini = []
    for doc in docs:
        data = doc.to_dict()
        immagini.append({
            "id": doc.id,
            "thumb": data.get("thumb"),
            "web": data.get("web"),
            "original": data.get("original"),
            "timestamp": data.get("timestamp")
        })

    return render_template('carica_immagini.html', immagini=immagini)



@admin_bp.route("/raccolte", methods=["GET"])
@admin_required
def gestione_raccolte():
    docs = g.db.collection("raccolte").stream()
    raccolte = [{"id": doc.id, **doc.to_dict()} for doc in docs]
    return render_template("gestione_raccolte.html", raccolte=raccolte)

@admin_bp.route("/immagini/tutte")
@admin_required
def tutte_immagini():
    docs = g.db.collection("foto_pubbliche").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(100).stream()
    immagini = []
    for doc in docs:
        data = doc.to_dict()
        immagini.append({
            "id": doc.id,
            "thumb": data.get("thumb"),
            "web": data.get("web"),
            "original": data.get("original")
        })
    return jsonify(immagini)


@admin_bp.route("/raccolte/crea", methods=["POST"])
@admin_required
def crea_raccolta_post():
    data = request.get_json()
    logger.debug("📥 JSON ricevuto: %s", data)

    if not data:
        logger.warning("Richiesta senza corpo JSON")
        return jsonify({"error": "Dati mancanti"}), 400

    nome = data.get("nome", "").strip()
    id_raccolta = nome.lower().replace(" ", "_")
    descrizione = data.get("descrizione", "").strip()
    immagini_ids = data.get("immagini", [])

    if not nome or not immagini_ids:
        logger.warning("Campi mancanti nella creazione della raccolta: nome=%s, immagini=%s", nome, immagini_ids)
        return jsonify({"error": "Nome e immagini obbligatori"}), 400

    # recupera la prima immagine per usarla come copertina
    copertina_url = None
    primo_id = immagini_ids[0]
    try:
        primo_doc = g.db.collection("foto_pubbliche").document(primo_id).get()
    except Exception:
        logger.exception("Errore Firestore durante il recupero dell'immagine '%s'", primo_id)
        return jsonify({"error": "Errore durante il recupero della copertina"}), 500

    if primo_doc.exists:
        primo_data = primo_doc.to_dict()
        copertina_url = primo_data.get("thumb")
    else:
        logger.warning("Documento immagine '%s' non trovato su Firestore", primo_id)
        return jsonify({"error": f"Immagine '{primo_id}' non trovata"}), 400

    try:
        raccolta_ref = g.db.collection("raccolte").document(id_raccolta)
        raccolta_ref.set({
            "nome": nome,
            "descrizione": descrizione,
            "copertina": copertina_url,
            "immagini": immagini_ids,
            "timestamp": firestore.SERVER_TIMESTAMP
        })

        # aggiorna ogni immagine con il campo raccolte[]
        for img_id in immagini_ids:
            img_ref = g.db.collection("foto_pubbliche").document(img_id)
            img_ref.update({"raccolte": firestore.ArrayUnion([id_raccolta])})
    except Exception:
        logger.exception("Errore Firestore durante la creazione della raccolta '%s'", id_raccolta)
        return jsonify({"error": "Errore durante il salvataggio della raccolta"}), 500

    return jsonify({"success": True}), 200

@admin_bp.route("/raccolte/elimina", methods=["POST"])
@admin_required
def elimina_raccolta():
    data = request.get_json()
    raccolta_id = data.get("id", "").strip()
    if not raccolta_id:
        return jsonify({"error": "ID mancante"}), 400

    raccolta_ref = g.db.collection("raccolte").document(raccolta_id)
    raccolta_doc = raccolta_ref.get()
    if not raccolta_doc.exists:
        return jsonify({"error": "Raccolta non trovata"}), 404

    immagini_ids = raccolta_doc.to_dict().get("immagini", [])
    for img_id in immagini_ids:
        g.db.collection("foto_pubbliche").document(img_id).update({
            "raccolte": firestore.ArrayRemove([raccolta_id])
        })

    raccolta_ref.delete()
    return jsonify({"success": True})

@admin_bp.route("/raccolte/dettaglio/<raccolta_id>")
@admin_required
def dettaglio_raccolta(raccolta_id):
    raccolta_ref = g.db.collection("raccolte").document(raccolta_id)
    raccolta_doc = raccolta_ref.get()

    if not raccolta_doc.exists:
        return jsonify({"error": "Raccolta non trovata"}), 404

    raccolta_data = raccolta_doc.to_dict()
    immagini_ids = raccolta_data.get("immagini", [])
    copertina = raccolta_data.get("copertina")

    immagini = []
    for img_id in immagini_ids:
        img_doc = g.db.collection("foto_pubbliche").document(img_id).get()
        if img_doc.exists:
            dati = img_doc.to_dict()
            immagini.append({
                "id": img_id,
                "thumb": dati.get("thumb"),
                "web": dati.get("web"),
                "original": dati.get("original")
            })

    return jsonify({
        "nome": raccolta_data.get("nome", raccolta_id),
        "descrizione": raccolta_data.get("descrizione", ""),
        "copertina": copertina,
        "immagini": immagini
    })

@admin_bp.route("/raccolte/update", methods=["POST"])
@admin_required
def aggiorna_raccolta():
    id_vecchio = request.form.get("id")
    nome_nuovo = request.form.get("nome", "").strip()
    descrizione = request.form.get("descrizione", "").strip()
    immagini_ids = request.form.getlist("immagini[]")
    file = request.files.get("copertina")

    logger.info("📥 ID raccolta originale: %s", id_vecchio)
    logger.info("📥 Nuovo nome: %s", nome_nuovo)
    logger.info("📥 Immagini ricevute: %s", immagini_ids)
    logger.info("📥 File copertina: %s", "presente" if file else "nessuno")

    if not id_vecchio or not nome_nuovo:
        return jsonify({"error": "ID o nome mancanti"}), 400

    id_nuovo = nome_nuovo.lower().replace(" ", "_")
    raccolta_ref_nuova = g.db.collection("raccolte").document(id_nuovo)
    client = storage.Client()
    bucket = client.bucket(g.bucket_name)
    
    # Copertina personalizzata (se inviata)
    if file:
        ext = file.filename.rsplit(".", 1)[-1].lower()
        filename = f"{id_nuovo}_cover.{ext}"
        safe_name = secure_filename(filename)
        blob = bucket.blob(f"foto/copertine/{safe_name}")
        blob.upload_from_file(file.stream, content_type=file.content_type)
        copertina_url = blob.public_url
    else:
        # Se non inviata nuova copertina, mantieni quella attuale (se presente)
        raccolta_doc_attuale = g.db.collection("raccolte").document(id_vecchio).get()
        copertina_url = raccolta_doc_attuale.to_dict().get("copertina") if raccolta_doc_attuale.exists else None

    # Aggiorna documento raccolta
    data = {
        "id": id_nuovo,
        "nome": nome_nuovo,
        "descrizione": descrizione,
        "copertina": copertina_url,
        "immagini": immagini_ids
    }

    raccolta_ref_nuova.set(data)
    logger.info("✅ Raccolta salvata con ID: %s", id_nuovo)
    logger.info("✅ Immagini nella raccolta: %s", immagini_ids)

    # Se il nome è cambiato, elimina la vecchia raccolta
    if id_vecchio != id_nuovo:
        logger.info("🧹 Eliminazione raccolta precedente: %s", id_vecchio)
        g.db.collection("raccolte").document(id_vecchio).delete()

    # 🔁 Aggiorna riferimenti raccolta nelle immagini
    # 🔁 Rimuovi il nome raccolta da tutte le immagini che NON devono più averlo
    for doc in g.db.collection("foto_pubbliche").stream():
        foto = doc.to_dict()
        foto_id = doc.id
        raccolte_attuali = foto.get("raccolte", [])

        aggiornata = False

        # Caso 1: l'immagine è stata rimossa da questa raccolta
        if id_nuovo not in immagini_ids and id_nuovo in raccolte_attuali:
            raccolte_attuali.remove(id_nuovo)
            aggiornata = True

        # Caso 2: l'immagine è stata appena aggiunta a questa raccolta
        if foto_id in immagini_ids and id_nuovo not in raccolte_attuali:
            raccolte_attuali.append(id_nuovo)
            aggiornata = True

        if aggiornata:
            g.db.collection("foto_pubbliche").document(foto_id).update({
                "raccolte": raccolte_attuali
            })
            logger.info("✅ Immagine %s aggiornata → raccolte: %s", foto_id, raccolte_attuali)


    return jsonify({
        "success": True,
        "id": id_nuovo,
        "immagini_salvate": immagini_ids
    })



@admin_bp.route("/postprocess", methods=["POST"])
@admin_required
def postprocess():
    data = request.get_json()
    foto_id = data.get("foto_id")
    filename = data.get("filename")


    if not foto_id or not filename:
        return jsonify({"error": "Dati mancanti"}), 400

    client = tasks_v2.CloudTasksClient()

    # ✅ Usa il progetto centrale (non quello del cliente)
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    queue = "upload-queue"
    location = "europe-west6"
    url = url_for("task.elabora_immagine", _external=True)

    # ✅ Include anche il cliente_id nel payload
    payload = json.dumps({
        "foto_id": foto_id,
        "filename": filename,
        "cliente_id": g.cliente_id  # 👈 ESSENZIALE
    })

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": url,
            "headers": {"Content-Type": "application/json"},
            "body": payload.encode(),
        },
    }

    parent = client.queue_path(project, location, queue)
    client.create_task(request={"parent": parent, "task": task})

    return jsonify({"queued": True})

@admin_bp.route("/signed-upload-url", methods=["POST"])
@admin_required
def signed_upload_url():
    data = request.get_json()
    filename = data.get("filename", "").strip()
    content_type = data.get("content_type", "application/octet-stream")


    if not filename:
        return jsonify({"error": "filename mancante"}), 400

    blob_path = f"foto/originals/{filename}"
    try:
        url = firma_url(g.bucket_name, blob_path, metodo="PUT", durata_minuti=10, content_type=content_type)
        public_url = f"https://storage.googleapis.com/{g.bucket_name}/{blob_path}"
        return jsonify({"url": url, "public_url": public_url})
    except Exception as e:
        logger.error("❌ Errore generazione signed URL: %s", e)
        return jsonify({"error": "errore generazione signed URL"}), 500
    
@admin_bp.route("/immagini", endpoint="lista_immagini")
@admin_required
def lista_immagini():
    from google.cloud import firestore
    
    query = request.args.get("query", "").strip().lower()

    immagini_ref = g.db.collection("foto_pubbliche").order_by(
        "timestamp", direction=firestore.Query.DESCENDING
    )
    immagini = immagini_ref.stream()

    dati = []
    for doc in immagini:
        item = doc.to_dict()
        item["id"] = doc.id

        raccolte = [r.lower() for r in item.get("raccolte", [])]
        if query and query not in item["id"].lower() and query not in raccolte:
            continue

        dati.append(item)

    return render_template("lista_immagini.html", immagini=dati)

@admin_bp.route("/immagini/elimina/<id>", methods=["POST"], endpoint="elimina_immagine")
@admin_required
def elimina_immagine(id):
    from google.cloud import storage, firestore

    
    doc = g.db.collection("foto_pubbliche").document(id).get()
    if not doc.exists:
        return redirect(url_for("admin.lista_immagini"))

    dati = doc.to_dict()
    filename = dati["original"].split("/")[-1]  # nome file esatto

    bucket = storage.Client().bucket(g.bucket_name)
    for path in [f"foto/originals/{filename}", f"foto/web/{filename}", f"foto/thumb/{filename}"]:
        blob = bucket.blob(path)
        if blob.exists():
            blob.delete()

    g.db.collection("foto_pubbliche").document(id).delete()
    return redirect(url_for("admin.lista_immagini"))


@admin_bp.route("/immagini/update_nome", methods=["POST"])
@admin_required
def aggiorna_nome_immagine():
    id_img = request.form.get("id")
    nuovo_nome = request.form.get("nome", "").strip()

    if not id_img:
        return jsonify({"error": "ID mancante"}), 400

    g.db.collection("foto_pubbliche").document(id_img).update({
        "nome": nuovo_nome
    })
    return jsonify({"success": True})


@admin_bp.route('/servizi')
@admin_required
def servizi():
    docs = g.db.collection('servizi').stream()
    servizi = [{**doc.to_dict(), 'id': doc.id} for doc in docs]
    return render_template('gestione_servizi.html', servizi=servizi)


@admin_bp.route('/servizi/crea', methods=['POST'])
@admin_required
def crea_servizio():
    nome = request.form.get('nome', '').strip()
    descrizione = request.form.get('descrizione', '').strip()
    costo = request.form.get('costo', '').strip()
    durata = request.form.get('durata', '').strip()
    immagine_url = request.form.get('immagine', '').strip()

    file = request.files.get('immagine_file')
    if file and file.filename:
        client = storage.Client()
        bucket = client.bucket(g.bucket_name)
        filename = secure_filename(file.filename)
        file_bytes = file.read()
        _, buffer, filename, content_type, _ = process_image(file_bytes, filename)
        blob = bucket.blob(f"servizi/{filename}")
        blob.upload_from_file(buffer, content_type=content_type)
        immagine_url = blob.public_url

    servizio_id = clean_servizio_id(nome)
    if not servizio_id:
        return jsonify({'error': 'Nome non valido'}), 400

    servizio = {
        'nome': nome,
        'descrizione': descrizione,
        'immagine': immagine_url,
        'costo': costo,
        'durata': durata,
    }
    g.db.collection('servizi').document(servizio_id).set(servizio)
    return jsonify({'success': True, 'id': servizio_id})



@admin_bp.route('/servizi/update', methods=['POST'])
@admin_required
def update_servizio():
    servizio_id = request.form.get('id')
    if not servizio_id:
        return jsonify({'error': 'ID mancante'}), 400

    nome = request.form.get('nome', '').strip()
    descrizione = request.form.get('descrizione', '').strip()
    costo = request.form.get('costo', '').strip()
    durata = request.form.get('durata', '').strip()
    immagine_url = request.form.get('immagine', '').strip()

    file = request.files.get('immagine_file')
    if file and file.filename:
        client = storage.Client()
        bucket = client.bucket(g.bucket_name)
        filename = secure_filename(file.filename)
        file_bytes = file.read()
        _, buffer, filename, content_type, _ = process_image(file_bytes, filename)
        blob = bucket.blob(f"servizi/{filename}")
        blob.upload_from_file(buffer, content_type=content_type)
        immagine_url = blob.public_url
    elif not immagine_url:
        doc = g.db.collection('servizi').document(servizio_id).get()
        if doc.exists:
            immagine_url = doc.to_dict().get('immagine', '')

    nuovo_id = clean_servizio_id(nome)


    update_data = {
        'nome': nome,
        'descrizione': descrizione,
        'costo': costo,
        'durata': durata,
        'immagine': immagine_url,
    }

    if nuovo_id and nuovo_id != servizio_id:
        g.db.collection('servizi').document(nuovo_id).set(update_data)
        g.db.collection('servizi').document(servizio_id).delete()
        servizio_id = nuovo_id
    else:
        g.db.collection('servizi').document(servizio_id).update(update_data)

    return jsonify({'success': True, 'id': servizio_id})



@admin_bp.route('/servizi/elimina', methods=['POST'])
@admin_required
def elimina_servizio():
    data = request.get_json() or request.form
    servizio_id = data.get('id')
    if not servizio_id:
        return jsonify({'error': 'ID mancante'}), 400
    g.db.collection('servizi').document(servizio_id).delete()
    return jsonify({'success': True})


@admin_bp.route('/servizi/immagini')
@admin_required
def lista_immagini_servizi():
    client = storage.Client()
    bucket = client.bucket(g.bucket_name)
    blobs = bucket.list_blobs(prefix='servizi/')
    immagini = [f'https://storage.googleapis.com/{g.bucket_name}/{b.name}' for b in blobs if not b.name.endswith('/')]
    return jsonify(immagini)


@admin_bp.route('/richieste-servizi')
@admin_required
def richieste_servizi():
    docs = (
        g.db.collection('appuntamenti')
        .where('stato', '==', 'richiesta')
        .order_by('data_ora')
        .stream()
    )
    richieste = [{**doc.to_dict(), 'id': doc.id} for doc in docs]
    return render_template('richieste_servizi.html', richieste=richieste)
