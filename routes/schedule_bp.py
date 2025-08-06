from flask import Blueprint, request, jsonify, render_template, g  # type: ignore
import logging
from services.calendar import add_event

schedule_bp = Blueprint("schedule", __name__)
logger = logging.getLogger(__name__)


@schedule_bp.route("/appuntamenti", methods=["GET"])
def prenota_servizi():
    servizi_docs = g.db.collection("servizi").stream()
    servizi = [{**doc.to_dict(), "id": doc.id} for doc in servizi_docs]
    disp_docs = g.db.collection("disponibilita").order_by("data_ora").stream()
    disponibilita = [{**doc.to_dict(), "id": doc.id} for doc in disp_docs]
    return render_template(
        "appuntamenti.html", servizi=servizi, disponibilita=disponibilita
    )


@schedule_bp.route("/appuntamenti", methods=["POST"])
def crea_appuntamento():
    data = request.get_json() or {}
    required = {"freelancer_id", "cliente_id", "data_ora", "servizi"}
    if not required.issubset(data):
        return jsonify({"error": "Dati mancanti"}), 400

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

    return jsonify({"success": True}), 201
