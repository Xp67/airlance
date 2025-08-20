"""Utility helpers for interacting with Firestore collections.

This module centralises CRUD operations so that other parts of the
application can depend on a consistent API when dealing with Firestore.
"""

from typing import Any, Dict, Optional

from google.cloud import firestore


# ---------------------------------------------------------------------------
# Generic helpers for existing collections
# ---------------------------------------------------------------------------


def utente_esiste(db: firestore.Client, email: str) -> bool:
    """Return ``True`` if a user with ``email`` exists."""

    return db.collection("utenti").document(email).get().exists


def crea_utente(db: firestore.Client, email: str, nome: str, picture: str) -> None:
    """Create a user document with the basic information provided."""

    db.collection("utenti").document(email).set(
        {
            "email": email,
            "nome": nome,
            "immagine": picture,
            "ruoli": ["utente"],  # default
        }
    )


def get_ruoli_utente(db: firestore.Client, email: str) -> list[str]:
    """Return the roles associated with ``email`` or an empty list."""

    doc_ref = db.collection("utenti").document(email)
    doc = doc_ref.get()
    if doc.exists:
        dati = doc.to_dict()
        return dati.get("ruoli", [])
    return []


def salva_link_foto(db: firestore.Client, foto_id: str, links: Dict[str, Any]) -> None:
    """Save the generated links for a photo."""

    doc_ref = db.collection("foto").document(foto_id)
    doc_ref.set(links)


# ---------------------------------------------------------------------------
# CRUD helpers for new collections
# ---------------------------------------------------------------------------

BOOKINGS = "bookings"
HOLDS = "holds"
SLOT_CACHE = "slot_cache"


# -- Bookings ---------------------------------------------------------------

def create_booking(db: firestore.Client, data: Dict[str, Any], booking_id: Optional[str] = None) -> str:
    """Create a booking document and return its ID."""

    collection = db.collection(BOOKINGS)
    if booking_id:
        collection.document(booking_id).set(data)
        return booking_id
    doc_ref = collection.add(data)[1]
    return doc_ref.id


def get_booking(db: firestore.Client, booking_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a booking document by ID."""

    doc = db.collection(BOOKINGS).document(booking_id).get()
    if doc.exists:
        return doc.to_dict()
    return None


def update_booking(db: firestore.Client, booking_id: str, updates: Dict[str, Any]) -> None:
    """Apply ``updates`` to the booking document with ``booking_id``."""

    db.collection(BOOKINGS).document(booking_id).update(updates)


def delete_booking(db: firestore.Client, booking_id: str) -> None:
    """Remove the booking document with ``booking_id``."""

    db.collection(BOOKINGS).document(booking_id).delete()


# -- Holds -----------------------------------------------------------------

def create_hold(db: firestore.Client, data: Dict[str, Any], hold_id: Optional[str] = None) -> str:
    """Create a hold document and return its ID."""

    collection = db.collection(HOLDS)
    if hold_id:
        collection.document(hold_id).set(data)
        return hold_id
    doc_ref = collection.add(data)[1]
    return doc_ref.id


def get_hold(db: firestore.Client, hold_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a hold document by ID."""

    doc = db.collection(HOLDS).document(hold_id).get()
    if doc.exists:
        return doc.to_dict()
    return None


def update_hold(db: firestore.Client, hold_id: str, updates: Dict[str, Any]) -> None:
    """Apply ``updates`` to the hold document with ``hold_id``."""

    db.collection(HOLDS).document(hold_id).update(updates)


def delete_hold(db: firestore.Client, hold_id: str) -> None:
    """Remove the hold document with ``hold_id``."""

    db.collection(HOLDS).document(hold_id).delete()


# -- Slot cache -------------------------------------------------------------

def set_slot_cache(db: firestore.Client, key: str, data: Dict[str, Any]) -> None:
    """Create or overwrite a slot cache entry with ``key``."""

    db.collection(SLOT_CACHE).document(key).set(data)


def get_slot_cache(db: firestore.Client, key: str) -> Optional[Dict[str, Any]]:
    """Retrieve a slot cache entry by ``key``."""

    doc = db.collection(SLOT_CACHE).document(key).get()
    if doc.exists:
        return doc.to_dict()
    return None


def update_slot_cache(db: firestore.Client, key: str, updates: Dict[str, Any]) -> None:
    """Update fields of a slot cache entry identified by ``key``."""

    db.collection(SLOT_CACHE).document(key).update(updates)


def delete_slot_cache(db: firestore.Client, key: str) -> None:
    """Delete the slot cache entry identified by ``key``."""

    db.collection(SLOT_CACHE).document(key).delete()
