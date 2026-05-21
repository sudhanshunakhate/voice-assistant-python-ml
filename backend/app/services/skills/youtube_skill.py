import re


def matches(text: str) -> bool:
    t = text.lower().strip()
    if re.search(r"\b(on|from|in)\s+youtube\b", t):
        return True
    if re.search(r"\byoutube\s*[.!?]*$", t):
        return True
    if re.search(r"^\s*youtube\s+", t) or re.search(r"^\s*yt\s+", t):
        return True
    if re.search(r"\bplay\s+youtube\b", t) or re.search(r"\byoutube\s+play\b", t):
        return True
    if re.search(r"^play\s+.+\s+on\s+youtube\b", t):
        return True
    return False


def extract_query(text: str) -> str:
    t = text.strip()
    t = re.sub(r"(?i)\s+on\s+youtube\s*[.!?]*$", "", t)
    t = re.sub(r"(?i)\s+from\s+youtube\s*[.!?]*$", "", t)
    t = re.sub(r"(?i)\s+in\s+youtube\s*[.!?]*$", "", t)
    t = re.sub(r"(?i)\byoutube\s*$", "", t)
    t = re.sub(r"(?i)^(?:play|open|find|search|watch)\s+", "", t)
    t = re.sub(r"(?i)^(?:yt|youtube)\s+", "", t)
    t = re.sub(r"(?i)\byoutube\b", " ", t)
    t = re.sub(r"(?i)\byt\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip(" ,.!?")
    return t[:200]


def handle(command: str) -> tuple[str, str | None, dict | None]:
    if not matches(command):
        return "", "", None
    q = extract_query(command)
    if not q:
        return "What song or video should I look up on YouTube?", "youtube", {"action": "none"}

    from app.services.youtube_client import first_video

    v = first_video(q)
    if not v:
        return f"I could not find a YouTube video for {q!r}. Try different words.", "youtube", {"action": "none"}

    return (
        f"Opening {v['title']!r} on YouTube in a new tab.",
        "youtube",
        {
            "action": "open_youtube",
            "url": v["url"],
            "video_id": v["id"],
            "title": v["title"],
        },
    )
