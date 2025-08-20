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
