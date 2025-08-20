from __future__ import annotations

import hashlib
from typing import Callable, Any, List


def _make_key(type_or_cart_hash: str, date_str: str) -> str:
    return f"{type_or_cart_hash}|{date_str}"


def find_contiguous_slots_for_cart(
    db,
    type_or_cart_hash: str,
    date_str: str,
    compute_slots: Callable[[], List[Any]],
):
    """Return contiguous slots for the given cart using a cache.

    The result is cached in the ``slot_cache`` collection using a key of the
    form ``TYPE_OR_CART_HASH|YYYY-MM-DD``.  ``compute_slots`` is only executed
    when the cache does not already contain a value for the requested key.
    """
    key = _make_key(type_or_cart_hash, date_str)
    doc_ref = db.collection("slot_cache").document(key)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict() or {}
        return data.get("slots", [])

    slots = compute_slots()
    doc_ref.set({"slots": slots})
    return slots


def invalidate_slot_cache(db, services: List[str], date_str: str) -> None:
    """Remove cached slots affected by the provided services and date."""
    if not services:
        return

    cart_hash = hashlib.sha1("|".join(sorted(services)).encode()).hexdigest()
    keys = [_make_key(s, date_str) for s in services]
    keys.append(_make_key(cart_hash, date_str))

    batch = db.batch()
    for key in keys:
        batch.delete(db.collection("slot_cache").document(key))
    batch.commit()
