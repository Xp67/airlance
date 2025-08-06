from flask import Blueprint, request, jsonify, render_template, g  # type: ignore
import logging
from services.calendar import add_event

schedule_bp = Blueprint("schedule", __name__)
logger = logging.getLogger(__name__)


@schedule_bp.route("/appuntamenti", methods=["GET"])
def lista_appuntamenti():
    docs = g.db.collection("appuntamenti").order_by("data_ora").stream()
    appuntamenti = [{"id": doc.id, **doc.to_dict()} for doc in docs]
    return render_template("appuntamenti.html", appuntamenti=appuntamenti)


@schedule_bp.route("/appuntamenti", methods=["POST"])
def crea_appuntamento():
    data = request.get_json() or {}
    required = {"freelancer_id", "cliente_id", "data_ora", "stato"}
    if not required.issubset(data):
        return jsonify({"error": "Dati mancanti"}), 400

    g.db.collection("appuntamenti").add({
        "freelancer_id": data["freelancer_id"],
        "cliente_id": data["cliente_id"],
        "data_ora": data["data_ora"],
        "stato": data["stato"],
    })

    try:
        add_event(g.db, data["freelancer_id"], {
            "summary": f"Appuntamento con {data['cliente_id']}",
            "start": {"dateTime": data["data_ora"]},
            "end": {"dateTime": data["data_ora"]},
        })
    except Exception as e:  # pragma: no cover - log but do not fail
        logger.warning("Impossibile sincronizzare evento calendario: %s", e)

    return jsonify({"success": True}), 201
