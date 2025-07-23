
from flask import Flask, session, request, render_template, g, send_from_directory, url_for # type: ignore
import config
from google.cloud import firestore, storage
from routes.auth import auth
from routes.user_bp import user_bp
from routes.admin_bp import admin_bp
from routes.task_bp import task_bp
import json
from jinja2 import ChoiceLoader, FileSystemLoader # type: ignore
import os




def carica_cliente():
    dominio = request.host.split(":")[0].lower().replace("www.", "").strip()
    db_centrale = firestore.Client()

    doc = db_centrale.collection("clienti_config").document(dominio).get()

    if doc.exists:
        cliente_config = doc.to_dict()
        g.config = cliente_config
        g.cliente_id = cliente_config["cliente_id"]
        g.db = firestore.Client(project="mireamakeup", database=cliente_config["firestore_db_id"])

        info_doc = g.db.collection("config").document("info").get()
        g.config_ui = info_doc.to_dict() if info_doc.exists else {}
        g.bucket_name = g.config_ui.get("bucket_name", f"foto{g.cliente_id}")
        
        if not hasattr(g, "template_loader_set") or g.template_loader_set != g.cliente_id:
            set_jinja_loader_per_cliente(g.cliente_id)
            g.template_loader_set = g.cliente_id
    else:
        g.config = {}
        g.cliente_id = "default"
        g.db = firestore.Client()
        g.config_ui = {}
        if not hasattr(g, "template_loader_set") or g.template_loader_set != "default":
            set_jinja_loader_per_cliente("default")
            g.template_loader_set = "default"


def set_jinja_loader_per_cliente(cliente_id):
    app.jinja_loader = ChoiceLoader([
        FileSystemLoader(os.path.join("clienti", cliente_id, "templates")),
        FileSystemLoader("templates")  # fallback globale
    ])
def verifica_bucket_clienti():
    print("🚀 Avvio verifica bucket per tutti i clienti...")
    client_storage = storage.Client()
    client_firestore = firestore.Client()

    clienti = client_firestore.collection("clienti_config").stream()

    for cliente in clienti:
        data = cliente.to_dict()
        cliente_id = data.get("cliente_id")
        firestore_db_id = data.get("firestore_db_id")

        if not cliente_id or not firestore_db_id:
            print(f"⚠️ Cliente senza ID o progetto Firestore: {data}")
            continue

        bucket_name = f"foto{cliente_id}"

        # Verifica se il bucket esiste
        if not client_storage.lookup_bucket(bucket_name):
            print(f"🆕 Creo bucket: {bucket_name}")
            bucket = client_storage.bucket(bucket_name)
            bucket.location = "europe-west6"
            client_storage.create_bucket(bucket)
            print(f"✅ Bucket creato: {bucket_name}")
        else:
            print(f"✅ Bucket già presente: {bucket_name}")

        # 🔁 Salva bucket_name nel Firestore del cliente (config > info)
        try:
            db_cliente = firestore.Client(project="mireamakeup", database=firestore_db_id)
            config_ref = db_cliente.collection("config").document("info")
            config_ref.set({"bucket_name": bucket_name}, merge=True)
            print(f"📌 Aggiornato campo bucket_name per {cliente_id} in {firestore_db_id}")
        except Exception as e:
            print(f"❌ Errore aggiornando config/info per {cliente_id}: {e}")
            
def file_cliente_esiste(cliente_id, path_locale):
    return os.path.exists(os.path.join("clienti", cliente_id, "static", path_locale))

app = Flask(__name__)
app.secret_key = "una-chiave-sicura"

verifica_bucket_clienti()

app.register_blueprint(auth)
app.register_blueprint(user_bp, url_prefix="/user")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(task_bp, url_prefix="/task")


@app.before_request
def before_all_requests():
    carica_cliente()


@app.route("/static_cliente/<path:filename>")
def static_cliente(filename):
    cliente_id = getattr(g, "cliente_id", None)
    if not cliente_id:
        return "Cliente non trovato", 404

    static_path = os.path.join("clienti", cliente_id, "static")
    return send_from_directory(static_path, filename)

@app.route('/')
def index():
    return render_template("index.html")

#CONTEXT ______________________________________________________________________

@app.context_processor
def inject_globals():
    cliente_id = getattr(g, "cliente_id", "default")
    config_ui = getattr(g, "config_ui", {})
    titolo_sito = config_ui.get("titolo_sito", "Airlance Fallback")
    # CSS
    tema_css_nome = config_ui.get("tema_css", "style.css")
    tema_css_path = f"css/{tema_css_nome}"

    if file_cliente_esiste(cliente_id, tema_css_path):
        tema_css = url_for("static_cliente", filename=tema_css_path)
    else:
        tema_css = url_for("static", filename=tema_css_path)

    # Favicon
    favicon_path = "logo/favicon.ico"
    if file_cliente_esiste(cliente_id, favicon_path):
        favicon_url = url_for("static_cliente", filename=favicon_path)
    else:
        favicon_url = url_for("static", filename=favicon_path)

    # Logo
    logo_path = "logo/logo.png"
    if file_cliente_esiste(cliente_id, logo_path):
        logo_url = url_for("static_cliente", filename=logo_path)
    else:
        logo_url = url_for("static", filename=logo_path)
        
    print("🧪 g.cliente_id =", getattr(g, "cliente_id", "N/A"))
    print("🧪 config_ui =", config_ui)
    print("🧪 titolo_sito =", titolo_sito)
    return {
        "FAVICON_URL": favicon_url,
        "LOGO_URL": logo_url,
        "tema_css": tema_css,
        "user": session.get("user"),
        "request": request,
        "WHITELIST": config.WHITELIST,
        "NOME_AZIENDA": config.NOME_AZIENDA,
        "POWERED_BY": config.POWERED_BY,
        "BUCKET_NAME": config.BUCKET_NAME,
        "FOLDER": config.FOLDER,
        "TITOLO_SITO": titolo_sito,
        "CLIENTE_ID": cliente_id,

    }

