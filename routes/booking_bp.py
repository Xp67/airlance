from flask import Blueprint, jsonify, g, session, current_app  # type: ignore
from datetime import datetime
import logging

booking_bp = Blueprint("booking", __name__)
logger = logging.getLogger(__name__)


def _generate_ics(event: dict, tenant: str) -> str:
    start = event.get("start_utc")
    end = event.get("end_utc", start)
    uid = f"{event['id']}@{tenant}"
    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return (
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "PRODID:-//Airlance//EN\n"
        "BEGIN:VEVENT\n"
        f"UID:{uid}\n"
        f"DTSTAMP:{dtstamp}\n"
        f"DTSTART:{start}\n"
        f"DTEND:{end}\n"
        f"SUMMARY:Booking {event['id']}\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )


def _send_email_with_ics(recipient: str, ics_content: str) -> None:
    """Placeholder email sender that logs the ICS payload."""
    logger.info("📧 Sending booking confirmation to %s", recipient)
    logger.debug("ICS content:\n%s", ics_content)


@booking_bp.route("/api/booking/confirm/<booking_id>", methods=["POST"])
def confirm_checkout(booking_id: str):
    booking_ref = g.db.collection("bookings").document(booking_id)
    booking_doc = booking_ref.get()
    if not booking_doc.exists:
        return jsonify({"error": "Booking not found"}), 404

    booking = booking_doc.to_dict()
    booking_ref.update({"status": "confirmed"})

    tenant = getattr(g, "cliente_id", "default")
    event = {
        "id": booking_id,
        "start_utc": booking.get("start_utc"),
        "end_utc": booking.get("end_utc", booking.get("start_utc")),
    }
    ics_content = _generate_ics(event, tenant)
    recipient = booking.get("email")
    if recipient:
        _send_email_with_ics(recipient, ics_content)

    return jsonify({"success": True})


@booking_bp.route("/api/booking/cancel/<booking_id>", methods=["POST"])
def cancel_booking(booking_id: str):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    booking_ref = g.db.collection("bookings").document(booking_id)
    booking_doc = booking_ref.get()
    if not booking_doc.exists:
        return jsonify({"error": "Booking not found"}), 404

    booking = booking_doc.to_dict()
    user_email = session["user"].get("email")
    user_roles = session["user"].get("roles", [])
    if booking.get("email") != user_email and "admin" not in user_roles:
        return jsonify({"error": "Forbidden"}), 403

    booking_ref.update({"status": "cancelled"})
    return jsonify({"success": True})


@booking_bp.route("/api/booking/feed.ics", methods=["GET"])
def public_ical_feed():
    tenant = getattr(g, "cliente_id", "default")
    bookings = (
        g.db.collection("bookings")
        .where("status", "==", "confirmed")
        .stream()
    )
    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    events = []
    for doc in bookings:
        data = doc.to_dict()
        start = data.get("start_utc")
        end = data.get("end_utc", start)
        events.append(
            "BEGIN:VEVENT\n"
            f"UID:{doc.id}@{tenant}\n"
            f"DTSTAMP:{dtstamp}\n"
            f"DTSTART:{start}\n"
            f"DTEND:{end}\n"
            f"SUMMARY:Booking {doc.id}\n"
            "END:VEVENT\n"
        )
    ical = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Airlance//EN\n"
        + "".join(events)
        + "END:VCALENDAR\n"
    )
    return current_app.response_class(ical, mimetype="text/calendar")
