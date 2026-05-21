import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from app.services.skills import youtube_skill
from app.services.youtube_client import first_video


def _parse_transport_command(text: str) -> str | None:
    t = text.lower().strip()
    if "pause music" in t or t == "pause":
        return "pause"
    if "next track" in t or t == "next":
        return "next"
    if "previous track" in t or "last track" in t or t == "previous":
        return "previous"
    if "stop music" in t or t == "stop":
        return "stop"
    return None


def _parse_play_query(text: str) -> tuple[str | None, str | None]:
    """Returns (mode, query) where mode is 'all' or 'query' or None."""
    t = text.lower().strip()
    if t.startswith("play the music of "):
        return "query", text[len("play the music of ") :].strip()
    if t.startswith("play the song of "):
        return "query", text[len("play the song of ") :].strip()
    if t.startswith("play music of "):
        return "query", text[len("play music of ") :].strip()
    if t.startswith("listen to "):
        q = text[len("listen to ") :].strip()
        return ("query", q) if q else (None, None)
    if t in ("play", "play music") or re.fullmatch(r"play\s+the\s+music", t):
        return "all", None
    if t.startswith("play music "):
        rest = text[11:].strip()  # preserve original casing for search
        if not rest:
            return "all", None
        return "query", rest
    if t.startswith("play "):
        rest = text[5:].strip()
        if not rest:
            return None, None
        if rest.lower() == "music":
            return "all", None
        if rest.lower().startswith("music "):
            return "query", rest[6:].strip()
        return "query", rest
    return None, None


def _open_youtube_for_query(q: str) -> tuple[str, str, dict]:
    query = (q or "").strip() or "popular music official audio"
    v = first_video(query)
    if not v:
        return (
            f"I could not find a YouTube video for {query!r}. Try different words.",
            "music",
            {"action": "none"},
        )
    return (
        f"Opening {v['title']!r} on YouTube in a new tab.",
        "music",
        {
            "action": "open_youtube",
            "url": v["url"],
            "video_id": v["id"],
            "title": v["title"],
        },
    )


def handle_music_intent(text: str, db: "Session") -> tuple[str, str | None, dict | None]:
    # Explicit phrasing: on YouTube, yt …, etc.
    if youtube_skill.matches(text):
        msg, _, payload = youtube_skill.handle(text)
        if payload:
            return msg, "music", dict(payload)
        if msg:
            return msg, "music", {"action": "none"}

    transport = _parse_transport_command(text)
    if transport == "pause":
        return "Pausing playback.", "music", {"action": "pause"}
    if transport == "next":
        return "Next track (use the YouTube tab for playlist controls).", "music", {"action": "next"}
    if transport == "previous":
        return "Previous track (use the YouTube tab for controls).", "music", {"action": "previous"}
    if transport == "stop":
        return "Stopping local player if it was running.", "music", {"action": "stop"}

    mode, query = _parse_play_query(text)
    if mode == "all":
        return _open_youtube_for_query("popular music official")
    if mode == "query" and query:
        return _open_youtube_for_query(query)

    return "", "", None


def matches(text: str) -> bool:
    if youtube_skill.matches(text):
        return True
    if _parse_transport_command(text):
        return True
    m, _ = _parse_play_query(text)
    return m is not None
