from flask import Blueprint, request, jsonify
from services import availability, booking

booking_api = Blueprint("booking_api", __name__)


@booking_api.route("/availability", methods=["GET"])
def get_availability():
    """Return availability filtered by optional service and date parameters."""
    service_id = request.args.get("service_id")
    date = request.args.get("date")
    slots = availability.get_availability(service_id=service_id, date=date)
    return jsonify(slots)


@booking_api.route("/booking", methods=["POST"])
def create_booking_route():
    """Create a new booking using the provided JSON payload."""
    data = request.get_json() or {}
    required = {"tenant_id", "staff_id", "resource_id", "start_utc", "end_utc"}
    if not required.issubset(data):
        return jsonify({"error": "Missing required fields"}), 400
    result = booking.create_booking(data)
    return jsonify(result), 201
