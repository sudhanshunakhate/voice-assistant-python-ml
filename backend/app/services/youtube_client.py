"""Search YouTube for videos (no API key; uses youtube-search)."""

from __future__ import annotations

from typing import Any


def search_videos(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    q = (query or "").strip()
    if not q:
        return []
    try:
        from youtube_search import YoutubeSearch
    except ImportError:
        return []

    raw = YoutubeSearch(q, max_results=min(max(1, max_results), 15)).to_dict()
    out: list[dict[str, Any]] = []
    for item in raw:
        vid = item.get("id")
        if not vid or not isinstance(vid, str) or len(vid) < 6:
            continue
        title = (item.get("title") or "Video").strip()
        out.append(
            {
                "id": vid,
                "title": title,
                "url": f"https://www.youtube.com/watch?v={vid}",
                "duration": item.get("duration"),
            }
        )
    return out


def first_video(query: str) -> dict[str, Any] | None:
    hits = search_videos(query, 1)
    return hits[0] if hits else None
