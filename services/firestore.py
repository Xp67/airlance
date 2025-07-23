from google.cloud import firestore

db = firestore.Client()
utenti_ref = db.collection("utenti")

def utente_esiste(email):
    return utenti_ref.document(email).get().exists

def crea_utente(email, nome, picture):
    utenti_ref.document(email).set({
        "email": email,
        "nome": nome,
        "immagine": picture,
        "ruoli": ["utente"]  # default
    })
def get_ruoli_utente(email: str):
    doc_ref = db.collection("utenti").document(email)
    doc = doc_ref.get()
    if doc.exists:
        dati = doc.to_dict()
        return dati.get("ruoli", [])
    return []

def salva_link_foto(foto_id, links: dict):
    doc_ref = db.collection("foto").document(foto_id)
    doc_ref.set(links)