from flask import Blueprint, redirect, request, session, url_for, render_template  # type: ignore
import requests  # type: ignore
import os
from services.firestore import utente_esiste, get_ruoli_utente

auth = Blueprint('auth', __name__)

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@auth.route("/login")
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = requests.Request('GET', authorization_endpoint, params={
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": url_for('auth.callback', _external=True),
        "scope": "openid email profile",
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent"
    }).prepare().url

    return redirect(request_uri)

@auth.route("/callback")
def callback():
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Scambio del codice per token
    token_res = requests.post(
        token_endpoint,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": url_for('auth.callback', _external=True),
            "grant_type": "authorization_code"
        },
    )

    if token_res.status_code != 200:
        return f"Errore nel token exchange: {token_res.text}", 400

    token_response = token_res.json()

    if "access_token" not in token_response:
        return f"Access token mancante. Risposta: {token_response}", 400

    # Recupero dati utente
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    response = requests.get(
        userinfo_endpoint,
        headers={"Authorization": f"Bearer {token_response['access_token']}"}
    )

    if response.status_code != 200:
        return f"Errore nel recupero userinfo: {response.text}", 400

    userinfo = response.json()

    if not userinfo.get("email_verified"):
        return "Utente non verificato", 400

    # ✅ Se l’utente è registrato, carica i ruoli e salva tutto in sessione
    if utente_esiste(userinfo["email"]):
        ruoli = get_ruoli_utente(userinfo["email"])

        session["user"] = {
            "email": userinfo["email"],
            "name": userinfo["name"],
            "picture": userinfo["picture"],
            "roles": ruoli
        }
       
    else:
        session["user"] = {
            "email": userinfo["email"],
            "name": userinfo["name"],
            "picture": userinfo["picture"],
        }
        return redirect("/")

@auth.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/")