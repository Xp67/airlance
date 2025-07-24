from flask import Blueprint, redirect, request, session, url_for, render_template, flash, jsonify, g  # type: ignore
from werkzeug.utils import secure_filename # type: ignore
from google.cloud import firestore, tasks_v2, storage
from datetime import datetime
import json
from werkzeug.utils import secure_filename # type: ignore
import os
from services.storage import firma_url
from services.decorators import admin_required






admin_bp = Blueprint('admin', __name__,url_prefix='/admin')


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
    print("📥 JSON ricevuto:", data)

    nome = data.get("nome", "").strip()
    id_raccolta = nome.lower().replace(" ", "_") 
    descrizione = data.get("descrizione", "").strip()
    immagini_ids = data.get("immagini", [])

    if not nome or not immagini_ids:
        return jsonify({"error": "Nome e immagini obbligatori"}), 400

    # recupera la prima immagine per usarla come copertina
    copertina_url = None
    primo_id = immagini_ids[0]
    primo_doc = g.db.collection("foto_pubbliche").document(primo_id).get()
    if primo_doc.exists:
        primo_data = primo_doc.to_dict()
        copertina_url = primo_data.get("thumb")
    else:
        print(f"⚠️ Documento immagine '{primo_id}' non trovato su Firestore")
        return jsonify({"error": f"Immagine '{primo_id}' non trovata"}), 400


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
        img_ref.update({
            "raccolte": firestore.ArrayUnion([id_raccolta])

        })

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

    print("📥 ID raccolta originale:", id_vecchio)
    print("📥 Nuovo nome:", nome_nuovo)
    print("📥 Immagini ricevute:", immagini_ids)
    print("📥 File copertina:", "presente" if file else "nessuno")

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
    print(f"✅ Raccolta salvata con ID: {id_nuovo}")
    print(f"✅ Immagini nella raccolta: {immagini_ids}")

    # Se il nome è cambiato, elimina la vecchia raccolta
    if id_vecchio != id_nuovo:
        print(f"🧹 Eliminazione raccolta precedente: {id_vecchio}")
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
            print(f"✅ Immagine {foto_id} aggiornata → raccolte: {raccolte_attuali}")


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
        print("❌ Errore generazione signed URL:", e)
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
    data = request.get_json() or request.form
    servizio = {
        'nome': data.get('nome', '').strip(),
        'descrizione': data.get('descrizione', '').strip(),
        'immagine': data.get('immagine', '').strip(),
        'costo': data.get('costo', '').strip(),
        'durata': data.get('durata', '').strip(),
    }
    g.db.collection('servizi').add(servizio)
    return jsonify({'success': True})


@admin_bp.route('/servizi/update', methods=['POST'])
@admin_required
def update_servizio():
    data = request.get_json() or request.form
    servizio_id = data.get('id')
    if not servizio_id:
        return jsonify({'error': 'ID mancante'}), 400
    update_data = {k: data.get(k) for k in ['nome', 'descrizione', 'immagine', 'costo', 'durata'] if k in data}
    g.db.collection('servizi').document(servizio_id).update(update_data)
    return jsonify({'success': True})


@admin_bp.route('/servizi/elimina', methods=['POST'])
@admin_required
def elimina_servizio():
    data = request.get_json() or request.form
    servizio_id = data.get('id')
    if not servizio_id:
        return jsonify({'error': 'ID mancante'}), 400
    g.db.collection('servizi').document(servizio_id).delete()
    return jsonify({'success': True})
