import re
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Reminder

_LIST_PHRASES = (
    "list reminders",
    "list alarms",
    "my reminders",
    "my alarms",
    "show reminders",
    "show alarms",
    "what are my reminders",
    "upcoming reminders",
    "upcoming alarms",
)

_CREATE_HINTS = (
    "remind me",
    "set a reminder",
    "set reminder",
    "set an alarm",
    "set a alarm",
    "set alarm",
    "create a reminder",
    "create reminder",
    "create an alarm",
    "create a alarm",
    "create alarm",
    "add a reminder",
    "add reminder",
    "add an alarm",
    "add a alarm",
    "add alarm",
    "reminder for",
    "reminder at",
    "reminder of",
    "alarm for",
    "alarm at",
    "alarm of",
)

# 10:00 AM, 3:30pm, 14:00 (24h)
_RE_12H_MM = re.compile(r"\b(\d{1,2}):(\d{2})\s*(am|pm)\b", re.IGNORECASE)
_RE_12H = re.compile(r"\b(\d{1,2})\s*(am|pm)\b", re.IGNORECASE)
_RE_24H = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")


def _to_24h(hour: int, ampm: str) -> int:
    ap = ampm.lower()
    if ap == "am":
        return 0 if hour == 12 else hour
    return 12 if hour == 12 else hour + 12


def _next_fire_at(hour: int, minute: int) -> datetime:
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


def parse_time_from_text(text: str) -> tuple[int, int] | None:
    m = _RE_12H_MM.search(text)
    if m:
        h, mn, ap = int(m.group(1)), int(m.group(2)), m.group(3)
        if not (0 <= h <= 12 and 0 <= mn <= 59):
            return None
        return _to_24h(h, ap), mn
    m = _RE_12H.search(text)
    if m:
        h, ap = int(m.group(1)), m.group(2)
        if not 1 <= h <= 12:
            return None
        return _to_24h(h, ap), 0
    m = _RE_24H.search(text)
    if m:
        h, mn = int(m.group(1)), int(m.group(2))
        if h > 23 or mn > 59:
            return None
        # Prefer 12h if also matched elsewhere; single match is fine
        return h, mn
    return None


def _extract_label(text: str) -> str:
    t = text.strip()
    low = t.lower()
    if " to " in low:
        idx = low.index(" to ")
        rest = t[idx + 4 :].strip()
        for rx in (_RE_12H_MM, _RE_12H, _RE_24H):
            rest = rx.sub("", rest).strip()
        rest = re.sub(r"\b(at|on|by|for)\b", "", rest, flags=re.I)
        rest = re.sub(r"\s+", " ", rest).strip(" ,.")
        if len(rest) >= 2:
            return rest[:500]
    # Strip times and common filler words
    cleaned = t
    for rx in (_RE_12H_MM, _RE_12H, _RE_24H):
        cleaned = rx.sub(" ", cleaned)
    for phrase in _CREATE_HINTS:
        cleaned = re.sub(re.escape(phrase), " ", cleaned, flags=re.I)
    cleaned = re.sub(
        r"\b(of|at|for|on|the|a|an|set|create|add|me|reminder|reminders|alarm|alarms|"
        r"today|tomorrow|i|need|please)\b",
        " ",
        cleaned,
        flags=re.I,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.")
    return cleaned[:500] if len(cleaned) >= 2 else "Reminder"


def matches_list(text: str) -> bool:
    t = text.lower().strip()
    return any(p in t for p in _LIST_PHRASES)


def matches_create(text: str) -> bool:
    t = text.lower()
    if any(h in t for h in _CREATE_HINTS):
        return True
    return ("reminder" in t or "alarm" in t) and any(
        x in t for x in ("set ", "create ", "add ", "schedule ")
    )


def list_reminders(db: Session) -> str:
    rows = (
        db.query(Reminder)
        .filter(Reminder.dismissed.is_(False))
        .filter(Reminder.fire_at >= datetime.now())
        .order_by(Reminder.fire_at.asc())
        .limit(20)
        .all()
    )
    if not rows:
        return "You have no upcoming reminders."
    lines = []
    for r in rows:
        lines.append(f"— {r.label} at {r.fire_at.strftime('%I:%M %p on %b %d')}")
    return "Here are your upcoming reminders:\n" + "\n".join(lines)


def create_reminder(text: str, db: Session) -> tuple[str, bool]:
    parsed = parse_time_from_text(text)
    if not parsed:
        return (
            "I could not find a time. Try: set a reminder or an alarm at 10:00 AM, "
            "or remind me to call mom at 3 PM.",
            False,
        )
    hour, minute = parsed
    fire_at = _next_fire_at(hour, minute)
    label = _extract_label(text)
    db.add(Reminder(label=label, fire_at=fire_at))
    db.commit()
    when = fire_at.strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
    day = fire_at.strftime("%A, %B %d")
    return (
        f"Done. I will remind you about {label!r} at {when} ({day}).",
        True,
    )


def handle(db: Session, command: str) -> tuple[str, str | None, dict | None]:
    if matches_list(command):
        return list_reminders(db), "reminder", None
    if matches_create(command):
        msg, ok = create_reminder(command, db)
        return msg, "reminder", {"created": ok}
    return "", "", None
