
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Iterable, Dict, Any
from google.cloud import firestore
import logging
from flask import g
from services.calendar import add_event

logger = logging.getLogger(__name__)


def create_booking(data: dict) -> dict:
    """Persist a booking request and sync with the calendar if possible."""
    g.db.collection("appuntamenti").add(
        {
            "freelancer_id": data["freelancer_id"],
            "cliente_id": data["cliente_id"],
            "data_ora": data["data_ora"],
            "servizi": data["servizi"],
            "stato": "richiesta",
        }
    )
    try:
        add_event(
            g.db,
            data["freelancer_id"],
            {
                "summary": f"Richiesta servizi {', '.join(data['servizi'])}",
                "start": {"dateTime": data["data_ora"]},
                "end": {"dateTime": data["data_ora"]},
            },
        )
    except Exception as e:  # pragma: no cover - log but do not fail
        logger.warning("Impossibile sincronizzare evento calendario: %s", e)
    return {"success": True}

def create_hold(
    db: firestore.Client,
    offer_id: str,
    seats: Iterable[str],
    ttl_seconds: int = 900,
) -> Dict[str, Any]:
    """Create a temporary hold on the requested seats.

    Holds are stored in the ``holds`` collection using a document ID derived from
    ``offer_id`` and ``seat``. The document contains an ``expires_at`` timestamp
    used by Firestore's TTL feature. Existing holds are checked in a transaction
    and removed if expired before creating the new hold.
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=ttl_seconds)
    transaction = db.transaction()

    @firestore.transactional
    def _tx(transaction: firestore.Transaction) -> Dict[str, Any]:
        for seat in seats:
            doc_id = f"{offer_id}_{seat}"
            doc_ref = db.collection("holds").document(doc_id)
            snapshot = doc_ref.get(transaction=transaction)
            if snapshot.exists:
                data = snapshot.to_dict()
                existing_exp = data.get("expires_at")
                if existing_exp and existing_exp > now:
                    raise ValueError(f"Seat {seat} already on hold")
                # hold expired, remove it so we can reuse the seat
                transaction.delete(doc_ref)
            transaction.set(
                doc_ref,
                {
                    "offer_id": offer_id,
                    "seat_id": seat,
                    "created_at": now,
                    # TTL field - Firestore will delete document automatically
                    "expires_at": expires_at,
                },
            )
        return {"expires_at": expires_at}

    return _tx(transaction)


def confirm_checkout(
    db: firestore.Client,
    booking_data: Dict[str, Any],
    idempotency_key: str,
) -> Dict[str, Any]:
    """Finalize a booking using an existing hold.

    The function ensures idempotency by storing the ``idempotency_key`` in a
    dedicated ``idempotency`` collection pointing to the created booking. Any
    subsequent call with the same key will return the original booking.
    Holds are verified inside a transaction to avoid conflicts and are deleted
    once the booking is confirmed.
    """
    now = datetime.now(timezone.utc)
    offer_id = booking_data["offer_id"]
    seats = booking_data["seats"]
    transaction = db.transaction()

    @firestore.transactional
    def _tx(transaction: firestore.Transaction) -> Dict[str, Any]:
        # Idempotency check
        idem_ref = db.collection("idempotency").document(idempotency_key)
        idem_snap = idem_ref.get(transaction=transaction)
        if idem_snap.exists:
            booking_id = idem_snap.to_dict().get("booking_id")
            booking_ref = db.collection("bookings").document(booking_id)
            booking_snap = booking_ref.get(transaction=transaction)
            if booking_snap.exists:
                return {**booking_snap.to_dict(), "id": booking_snap.id}
            return {"id": booking_id}

        # Validate holds and remove expired ones if necessary
        for seat in seats:
            hold_ref = db.collection("holds").document(f"{offer_id}_{seat}")
            hold_snap = hold_ref.get(transaction=transaction)
            if not hold_snap.exists:
                raise ValueError(f"Hold for seat {seat} not found")
            data = hold_snap.to_dict()
            exp = data.get("expires_at")
            if exp and exp < now:
                # remove expired hold and abort
                transaction.delete(hold_ref)
                raise ValueError(f"Hold for seat {seat} expired")

        # Create booking
        booking_ref = db.collection("bookings").document()
        transaction.set(
            booking_ref,
            {**booking_data, "created_at": now, "idempotency_key": idempotency_key},
        )
        transaction.set(idem_ref, {"booking_id": booking_ref.id, "created_at": now})

        # Remove holds now that the booking is confirmed
        for seat in seats:
            hold_ref = db.collection("holds").document(f"{offer_id}_{seat}")
            transaction.delete(hold_ref)

        return {**booking_data, "id": booking_ref.id}

    return _tx(transaction)



