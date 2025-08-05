from flask import Blueprint, render_template, g
import random

public_bp = Blueprint('public', __name__)

@public_bp.route('/contatti')
def contatti():
    return render_template('contatti.html')

@public_bp.route('/servizi')
def servizi():
    servizi_ref = g.db.collection('servizi').stream()
    servizi = [doc.to_dict() for doc in servizi_ref]
    return render_template('servizi.html', servizi=servizi)

@public_bp.route('/portfolio')
def portfolio():
    # Fetch collections
    raccolte_ref = g.db.collection('raccolte').stream()
    raccolte = [doc.to_dict() for doc in raccolte_ref]

    # Fetch all images and shuffle them
    images_ref = g.db.collection('foto_pubbliche').stream()
    images = [doc.to_dict() for doc in images_ref]
    random.shuffle(images)

    return render_template('portfolio.html', raccolte=raccolte, images=images)
