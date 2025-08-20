from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build  # type: ignore
from google.auth.transport.requests import Request
import json

from .calendars import ensure_event_timezone

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def get_credentials(db, user_id: str) -> Credentials:
    doc = db.collection("tokens").document(user_id).get()
    if not doc.exists:
        raise ValueError("Token non trovato per l'utente")
    token_info = doc.to_dict()
    creds = Credentials.from_authorized_user_info(token_info, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        db.collection("tokens").document(user_id).set(json.loads(creds.to_json()))
    return creds


def add_event(
    db,
    user_id: str,
    event_body: dict,
    timezone: str | None = None,
) -> dict:
    """Inserisce un evento nel calendario di Google.

    Args:
        db: istanza di firestore.
        user_id: identificativo dell'utente.
        event_body: payload compatibile con l'API di Google Calendar.
        timezone: timezone da applicare agli orari ``start`` ed ``end``.
    """

    if timezone:
        event_body = ensure_event_timezone(event_body, timezone)

    creds = get_credentials(db, user_id)
    service = build("calendar", "v3", credentials=creds)
    return service.events().insert(calendarId="primary", body=event_body).execute()
