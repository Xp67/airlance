from google.cloud import firestore


def utente_esiste(db, email):
    return db.collection("utenti").document(email).get().exists

def crea_utente(db, email, nome, picture):
    db.collection("utenti").document(email).set({
        "email": email,
        "nome": nome,
        "immagine": picture,
        "ruoli": ["utente"]  # default
    })
def get_ruoli_utente(db, email: str):
    doc_ref = db.collection("utenti").document(email)
    doc = doc_ref.get()
    if doc.exists:
        dati = doc.to_dict()
        return dati.get("ruoli", [])
    return []

def salva_link_foto(db, foto_id, links: dict):
    doc_ref = db.collection("foto").document(foto_id)
    doc_ref.set(links)