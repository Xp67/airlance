from __future__ import annotations

"""Utility per il calcolo delle disponibilità.

Questo modulo fornisce alcune funzioni di supporto per individuare gli slot di
prenotazione disponibili tenendo conto dei calendari di staff e risorse e delle
prenotazioni già registrate nella collezione ``bookings/*``.
"""

from datetime import datetime, timedelta
from typing import List, Mapping, Sequence, Tuple

TimeWindow = Tuple[datetime, datetime]


def compute_cart_total_duration(cart: Sequence[Mapping[str, object]]) -> timedelta:
    """Calcola la durata complessiva di un carrello.

    Ogni elemento del carrello deve esporre un campo ``duration`` espresso in
    minuti oppure come ``timedelta``. La funzione somma tali durate e restituisce
    il totale come ``timedelta``.

    Args:
        cart: Sequenza di elementi del carrello.

    Returns:
        ``timedelta`` rappresentante la durata complessiva.
    """

    total_minutes = 0
    for item in cart:
        duration = item.get("duration")
        if isinstance(duration, timedelta):
            total_minutes += int(duration.total_seconds() // 60)
        elif duration is not None:
            total_minutes += int(duration)
    return timedelta(minutes=total_minutes)


def _subtract_window(base: TimeWindow, block: TimeWindow) -> List[TimeWindow]:
    """Sottrae ``block`` da ``base`` restituendo le parti libere."""

    start, end = base
    b_start, b_end = block
    if b_end <= start or b_start >= end:
        return [base]
    windows: List[TimeWindow] = []
    if b_start > start:
        windows.append((start, min(b_start, end)))
    if b_end < end:
        windows.append((max(start, b_end), end))
    return windows


def list_base_windows(
    calendar_windows: Sequence[TimeWindow], bookings: Sequence[TimeWindow]
) -> List[TimeWindow]:
    """Restituisce le finestre disponibili rimuovendo i conflitti delle prenotazioni.

    Gli intervalli in ``calendar_windows`` rappresentano le disponibilità di
    base del calendario di uno staff o di una risorsa. Gli intervalli in
    ``bookings`` rappresentano le prenotazioni presenti su ``bookings/*`` che
    devono essere esclusi.

    Args:
        calendar_windows: Sequenza di finestre di disponibilità.
        bookings: Sequenza di intervalli occupati dalle prenotazioni.

    Returns:
        Lista di ``TimeWindow`` disponibili e privi di conflitti.
    """

    free: List[TimeWindow] = []
    for window in sorted(calendar_windows):
        fragments = [window]
        for booking in bookings:
            new_fragments: List[TimeWindow] = []
            for fragment in fragments:
                new_fragments.extend(_subtract_window(fragment, booking))
            fragments = new_fragments
            if not fragments:
                break
        free.extend(fragments)
    return sorted(free)


def intersect_staff_resource_windows(
    staff_windows: Sequence[TimeWindow], resource_windows: Sequence[TimeWindow]
) -> List[TimeWindow]:
    """Calcola l'intersezione tra le finestre di staff e risorsa.

    Args:
        staff_windows: Finestre disponibili per il membro dello staff.
        resource_windows: Finestre disponibili per la risorsa.

    Returns:
        Lista di ``TimeWindow`` in cui staff e risorsa sono entrambi liberi.
    """

    intersections: List[TimeWindow] = []
    i = j = 0
    staff = sorted(staff_windows)
    resource = sorted(resource_windows)
    while i < len(staff) and j < len(resource):
        s_start, s_end = staff[i]
        r_start, r_end = resource[j]
        start = max(s_start, r_start)
        end = min(s_end, r_end)
        if start < end:
            intersections.append((start, end))
        if s_end <= r_end:
            i += 1
        else:
            j += 1
    return intersections


def find_contiguous_slots_for_cart(
    windows: Sequence[TimeWindow],
    total_duration: timedelta,
    step: timedelta = timedelta(minutes=15),
) -> List[TimeWindow]:
    """Trova gli slot contigui sufficientemente lunghi per il carrello.

    Args:
        windows: Finestre di disponibilità (prive di conflitti).
        total_duration: Durata complessiva richiesta per il carrello.
        step: Passo con cui scorrere la finestra alla ricerca degli slot.

    Returns:
        Lista di ``TimeWindow`` che possono contenere tutte le prenotazioni del
        carrello.
    """

    slots: List[TimeWindow] = []
    for start, end in windows:
        cursor = start
        while cursor + total_duration <= end:
            slot_end = cursor + total_duration
            slots.append((cursor, slot_end))
            cursor += step
    return slots
