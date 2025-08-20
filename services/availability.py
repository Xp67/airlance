from flask import g
from typing import List, Dict, Optional


def get_availability(service_id: Optional[str] = None, date: Optional[str] = None) -> List[Dict]:
    """Return available slots optionally filtered by service and date.

    Parameters
    ----------
    service_id: optional id of the service to filter on.
    date: optional ISO date string to filter on (YYYY-MM-DD).
    """
    query = g.db.collection("disponibilita")
    if service_id:
        query = query.where("servizio_id", "==", service_id)
    if date:
        query = query.where("data", "==", date)
    disp_docs = query.order_by("data_ora").stream()
    return [{**doc.to_dict(), "id": doc.id} for doc in disp_docs]
