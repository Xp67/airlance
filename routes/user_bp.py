from flask import Blueprint, redirect, request, session, url_for, render_template, g, flash  # type: ignore
from werkzeug.utils import secure_filename  # type: ignore
from google.cloud import storage
from services.image_utils import process_image
import json


user_bp = Blueprint('user', __name__, url_prefix='/user')


@user_bp.route('/profilo')
def profilo():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('profilo.html')


@user_bp.route('/profilo', methods=['POST'])
def aggiorna_profilo():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    nome = request.form.get('nome', '').strip()
    if not nome:
        flash('Nome obbligatorio', 'error')
        return redirect(url_for('user.profilo'))

    preferenze_raw = request.form.get('preferenze', '')
    try:
        preferenze = json.loads(preferenze_raw) if preferenze_raw else None
    except json.JSONDecodeError:
        flash('Preferenze non valide', 'error')
        return redirect(url_for('user.profilo'))

    immagine_file = request.files.get('immagine')
    immagine_url = None
    if immagine_file and immagine_file.filename:
        client = storage.Client()
        bucket = client.bucket(g.bucket_name)
        filename = secure_filename(immagine_file.filename)
        file_bytes = immagine_file.read()
        try:
            _, buffer, filename, content_type, _ = process_image(file_bytes, filename)
        except Exception:
            flash('Immagine non valida', 'error')
            return redirect(url_for('user.profilo'))
        email = session['user']['email']
        safe_email = email.replace('@', '_').replace('.', '_')
        blob = bucket.blob(f"utenti/{safe_email}/{filename}")
        blob.upload_from_file(buffer, content_type=content_type)
        immagine_url = blob.public_url

    email = session['user']['email']
    data = {'nome': nome}
    if immagine_url:
        data['immagine'] = immagine_url
    if preferenze is not None:
        data['preferenze'] = preferenze
    g.db.collection('utenti').document(email).set(data, merge=True)

    session['user']['name'] = nome
    if immagine_url:
        session['user']['picture'] = immagine_url
    if preferenze is not None:
        session['user']['preferenze'] = preferenze

    return redirect(url_for('user.profilo'))

