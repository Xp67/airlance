from __future__ import annotations

"""Utility e parser per la gestione dei calendari.

Questo modulo offre funzioni per interpretare le regole settimanali e le
eccezioni di disponibilità oltre a utility per la conversione dei timezone e
la gestione dei lead time.
"""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from typing import Any, Dict, Iterable, List, Optional


# ----------------------------------------------------------------------------
# Dataclass di supporto
# ----------------------------------------------------------------------------

@dataclass
class WeeklyRule:
    """Rappresenta una regola ricorrente di disponibilità settimanale.

    Attributes:
        weekday: Giorno della settimana (0=lunedì ... 6=domenica)
        start: Ora di inizio con timezone associato
        end: Ora di fine con timezone associato
    """

    weekday: int
    start: time
    end: time


@dataclass
class ExceptionRule:
    """Rappresenta un'eccezione puntuale alla disponibilità."""

    start: datetime
    end: datetime


_DAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _parse_time(value: str) -> time:
    """Parsa una stringa HH:MM in :class:`~datetime.time`."""

    hour, minute = map(int, value.split(":", 1))
    return time(hour=hour, minute=minute)


def _parse_weekday(value: Any) -> int:
    """Converte un giorno della settimana in un intero [0-6]."""

    if isinstance(value, int):
        if 0 <= value <= 6:
            return value
        raise ValueError("weekday fuori range 0-6")
    if isinstance(value, str):
        name = value.strip().lower()
        if name in _DAY_MAP:
            return _DAY_MAP[name]
    raise ValueError(f"weekday non valido: {value}")


# ----------------------------------------------------------------------------
# Parser
# ----------------------------------------------------------------------------

def parse_weekly_rules(rules: Iterable[Dict[str, Any]], tz: str) -> List[WeeklyRule]:
    """Parsa un elenco di regole settimanali.

    Ogni regola deve contenere ``weekday`` (int o nome inglese) e gli orari
    ``start`` e ``end`` nel formato ``HH:MM``.
    """

    zone = ZoneInfo(tz)
    parsed: List[WeeklyRule] = []
    for rule in rules:
        weekday = _parse_weekday(rule["weekday"])
        start = _parse_time(rule["start"]).replace(tzinfo=zone)
        end = _parse_time(rule["end"]).replace(tzinfo=zone)
        parsed.append(WeeklyRule(weekday=weekday, start=start, end=end))
    return parsed


def parse_exceptions(exceptions: Iterable[Dict[str, Any]], tz: str) -> List[ExceptionRule]:
    """Parsa le eccezioni di disponibilità.

    Ogni eccezione richiede ``date`` nel formato ISO ``YYYY-MM-DD`` e opzionali
    ``start`` e ``end`` ``HH:MM``. Se mancanti l'intera giornata è considerata
    non disponibile.
    """

    zone = ZoneInfo(tz)
    parsed: List[ExceptionRule] = []
    for ex in exceptions:
        base_date = datetime.fromisoformat(ex["date"]).date()
        start_time = _parse_time(ex.get("start", "00:00"))
        end_time = _parse_time(ex.get("end", "23:59"))
        start = datetime.combine(base_date, start_time, zone)
        end = datetime.combine(base_date, end_time, zone)
        parsed.append(ExceptionRule(start=start, end=end))
    return parsed


# ----------------------------------------------------------------------------
# Utility
# ----------------------------------------------------------------------------

def to_timezone(dt: datetime, tz: str) -> datetime:
    """Converte ``dt`` nel timezone ``tz``.

    Se ``dt`` è naive viene assegnato direttamente il timezone richiesto.
    """

    zone = ZoneInfo(tz)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=zone)
    return dt.astimezone(zone)


def is_within_lead_time(
    dt: datetime,
    *,
    lead_time_min: Optional[int] = None,
    lead_time_max: Optional[int] = None,
    now: Optional[datetime] = None,
) -> bool:
    """Verifica se ``dt`` rientra tra i lead time min/max specificati.

    ``lead_time_min`` e ``lead_time_max`` sono espressi in minuti.
    """

    reference = now or datetime.now(tz=dt.tzinfo)
    if lead_time_min is not None and dt < reference + timedelta(minutes=lead_time_min):
        return False
    if lead_time_max is not None and dt > reference + timedelta(minutes=lead_time_max):
        return False
    return True


def ensure_event_timezone(event: Dict[str, Any], tz: str) -> Dict[str, Any]:
    """Restituisce ``event`` assicurando che ``start`` ed ``end`` siano nel timezone.

    ``event`` è modificato superficialmente e può contenere campi ``dateTime``
    in formato ISO8601.
    """

    zone = ZoneInfo(tz)
    result = event.copy()
    for key in ("start", "end"):
        if key in result and isinstance(result[key], dict):
            dt_str = result[key].get("dateTime")
            if dt_str:
                dt = datetime.fromisoformat(dt_str)
                result[key] = {"dateTime": to_timezone(dt, tz).isoformat()}
    return result
