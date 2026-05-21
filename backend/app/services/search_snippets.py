"""
Web snippets for S.U.K.U: Google Custom Search (optional), DuckDuckGo text (lite/html),
then DuckDuckGo Instant Answer JSON (often works when HTML search returns 429/202).
"""

from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import quote

import httpx

from app.config import settings

_WIKI_UA = "SUKU-Assistant/1.0 (local voice assistant; +https://github.com/)"


def _clip_first_sentence(text: str, max_len: int) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    cut = text
    for sep in (". ", "? ", "! "):
        idx = cut.find(sep)
        if 12 <= idx <= 220:
            cut = cut[: idx + 1].strip()
            break
    if len(cut) > max_len:
        cut = cut[: max_len - 1].rsplit(" ", 1)[0] + "…"
    return cut


def _clip_smart(text: str, max_len: int, max_sentences: int = 4) -> str:
    """Up to max_sentences sentence boundaries, capped at max_len (word boundary)."""
    text = (text or "").strip()
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    out_parts: list[str] = []
    rest = text
    for _ in range(max(1, max_sentences)):
        if len(" ".join(out_parts)) >= max_len - 40:
            break
        best = -1
        for sep in (". ", "? ", "! "):
            i = rest.find(sep)
            if i >= 10 and (best < 0 or i < best):
                best = i
        if best < 0:
            break
        out_parts.append(rest[: best + 1].strip())
        rest = rest[best + 2 :].strip()
    out = " ".join(out_parts) if out_parts else text
    if len(out) > max_len:
        out = out[: max_len - 1].rsplit(" ", 1)[0] + "…"
    elif rest and len(out) + len(rest) + 1 <= max_len:
        out = (out + " " + rest).strip()
        if len(out) > max_len:
            out = out[: max_len - 1].rsplit(" ", 1)[0] + "…"
    return out


def _parse_wanted_count(query: str) -> int | None:
    """e.g. 'top 5 artists' -> 5 (for tighter formatting, not as a guarantee of real ranks)."""
    ql = query.lower()
    m = re.search(r"\b(?:top|first)\s+(\d+)\b", ql)
    if m:
        return max(1, min(int(m.group(1)), 10))
    m = re.search(r"\b(\d+)\s+(?:top|best|biggest|largest|main)\b", ql)
    if m:
        return max(1, min(int(m.group(1)), 10))
    return None


def _format_results(rows: list[dict[str, Any]], query: str = "") -> str:
    """
    Search snippets: longer excerpts (multi-sentence) and higher total budget for readout / display.
    For 'top N' questions, still clarifies that order is not one official global ranking.
    """
    want = _parse_wanted_count(query)
    max_items = min(max(want or 6, 8), 10)
    title_cap = 240 if want else 220
    body_cap = 520 if want else 480
    chunk_cap = 720 if want else 680
    max_total = 4200 if want else 3800

    lines: list[str] = []
    total = 0
    for r in rows:
        if len(lines) >= max_items:
            break
        title = (r.get("title") or "").strip()
        body = (r.get("snippet") or r.get("body") or "").strip()
        if not title and not body:
            continue

        title_s = _clip_smart(title, title_cap, 2)
        body_s = _clip_smart(body, body_cap, 5) if body else ""
        if title_s and body_s:
            if body_s.lower() in title_s.lower() or title_s.lower() in body_s.lower():
                chunk = title_s
            else:
                chunk = f"{title_s} - {body_s}"
        elif title_s:
            chunk = title_s
        else:
            chunk = body_s
        if not chunk:
            continue
        if len(chunk) > chunk_cap:
            chunk = chunk[: chunk_cap - 1].rsplit(" ", 1)[0] + "…"

        lines.append(f"- {chunk}")
        total += len(chunk)
        if total >= max_total:
            break

    if not lines:
        return "I found results but no short text to read out. Try a shorter question."

    if want:
        head = (
            "Charts and sites disagree on exact order, so this is not one official ranking - "
            "here are longer snippets from what turned up:\n"
        )
    else:
        head = "Here's what I found:\n"
    return head + "\n".join(lines)


def _google_custom_search(query: str) -> list[dict[str, Any]] | None:
    key = settings.google_search_api_key
    cx = settings.google_cse_id
    if not key or not cx:
        return None
    try:
        with httpx.Client(timeout=25.0) as client:
            r = client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={"key": key, "cx": cx, "q": query, "num": 10},
            )
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError:
        return None
    except Exception:
        return None
    items = data.get("items") or []
    out: list[dict[str, Any]] = []
    for it in items:
        out.append(
            {
                "title": it.get("title") or "",
                "snippet": it.get("snippet") or "",
            }
        )
    return out or None


def _search_query_variants(q: str) -> list[str]:
    """Broader / alternate phrasing when the exact question returns no DDG payload."""
    q = q.strip()
    if not q:
        return []
    ql = q.lower()
    variants = [q]
    if any(w in ql for w in ("artist", "artists", "musician", "musicians", "singer", "singers", "band", "bands")):
        variants.extend(
            [
                "Billboard Artist 100 chart",
                "biggest music artists in the world 2025",
                "most streamed artists Spotify worldwide",
                "list of best-selling music artists",
            ]
        )
    if re.search(r"\b(?:top|first)\s+\d+\b", ql):
        variants.append(re.sub(r"\b(?:top|first)\s+\d+\b", "top 10", q, count=1, flags=re.I))
    seen: set[str] = set()
    out: list[str] = []
    for v in variants:
        v = v.strip()
        key = v.lower()
        if v and key not in seen:
            seen.add(key)
            out.append(v)
    return out[:8]


def _wikipedia_snippet(query: str) -> str | None:
    """
    Last-resort factual text (Wikimedia REST + search API). Requires descriptive User-Agent.
    """
    candidates = [query.strip()[:120]]
    ql = query.lower()
    if any(w in ql for w in ("artist", "music", "singer", "band")):
        candidates = [
            "List of best-selling music artists",
            "Lists of music artists",
            *candidates,
        ]
    headers = {"User-Agent": _WIKI_UA, "Accept": "application/json"}
    try:
        with httpx.Client(timeout=18.0, headers=headers) as client:
            for c in candidates:
                c = c.strip()
                if len(c) < 2:
                    continue
                sr = client.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": c,
                        "srlimit": "2",
                        "format": "json",
                    },
                )
                if sr.status_code != 200:
                    continue
                hits = sr.json().get("query", {}).get("search") or []
                for h in hits:
                    title = (h.get("title") or "").strip()
                    if not title:
                        continue
                    path = quote(title.replace(" ", "_"), safe="")
                    su = client.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{path}")
                    if su.status_code != 200:
                        continue
                    data = su.json()
                    extract = (data.get("extract") or "").strip()
                    if not extract or data.get("type") == "disambiguation":
                        continue
                    clip = extract[:650]
                    if len(extract) > 650:
                        clip = clip.rsplit(" ", 1)[0] + "…"
                    return (
                        "Wikipedia fallback (search engines were unavailable):\n"
                        f"{clip}\n"
                        "Say ‘open Search page’ or try again in a minute for live web results."
                    )
    except Exception:
        return None
    return None


def _duckduckgo_text_search(query: str) -> list[dict[str, Any]] | None:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return None

    # Try lite and html explicitly (fresh client each time = new TLS fingerprint).
    backends = ("lite", "html", "lite", "html", "lite", "html", "lite")
    for attempt, backend in enumerate(backends):
        try:
            if attempt:
                time.sleep(1.0 + attempt * 0.28)
            with DDGS(timeout=28) as ddgs:
                raw = list(ddgs.text(query, max_results=10, backend=backend))
            if raw:
                return [
                    {"title": x.get("title") or "", "body": x.get("body") or ""}
                    for x in raw
                ]
        except Exception:
            continue
    return None


def _collect_related_topics(data: dict[str, Any], limit: int = 6) -> list[str]:
    out: list[str] = []
    for item in data.get("RelatedTopics") or []:
        if len(out) >= limit:
            break
        if isinstance(item, dict):
            t = (item.get("Text") or "").strip()
            if t:
                out.append(t)
            for sub in item.get("Topics") or []:
                if len(out) >= limit:
                    break
                if isinstance(sub, dict):
                    st = (sub.get("Text") or "").strip()
                    if st:
                        out.append(st)
    return out


def _compact_instant_response(text: str, query: str) -> str:
    """Trim instant-answer blobs for voice; drop long 'also related' tails for list-style questions."""
    want = _parse_wanted_count(query)
    if not want:
        return text[:1200] + ("…" if len(text) > 1200 else "")
    # Ranking-style: keep only first paragraph / sentence block
    first = text.split("\n\n")[0].strip()
    return _clip_first_sentence(first, 320)


def _duckduckgo_instant_answer(query: str) -> str | None:
    """
    DuckDuckGo Instant Answer API — different path than HTML scrape; often returns
    AbstractText even when html.duckduckgo.com rate-limits. May respond with HTTP 202
    and still include a JSON body.
    """
    q = (query or "").strip()
    if not q:
        return None
    try:
        with httpx.Client(
            timeout=20.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
                "Accept": "application/json,text/plain,*/*",
            },
        ) as client:
            r = client.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": q,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1,
                },
            )
        try:
            data = r.json()
        except Exception:
            return None
    except Exception:
        return None

    if not isinstance(data, dict):
        return None

    parts: list[str] = []
    heading = (data.get("Heading") or "").strip()
    abstract = (data.get("AbstractText") or data.get("Abstract") or "").strip()
    if abstract:
        if heading and heading.lower() not in abstract.lower()[: min(100, len(abstract))]:
            parts.append(f"{heading}: {abstract}")
        else:
            parts.append(abstract)

    answer = (data.get("Answer") or "").strip()
    if answer:
        blob = "\n".join(parts)
        if answer.lower() not in blob.lower():
            parts.append(answer)

    definition = (data.get("Definition") or "").strip()
    if definition and definition.lower() not in "\n".join(parts).lower():
        parts.append(definition)

    related = _collect_related_topics(data, 6)

    want = _parse_wanted_count(q)

    if parts:
        main = "\n\n".join(parts)
        if related and not want:
            rel_short = [
                _clip_first_sentence(t, 100) for t in related[:3] if t
            ]
            if rel_short:
                main += "\n\nAlso related:\n" + "\n".join(f"- {x}" for x in rel_short)
        out = main[:1200] + ("…" if len(main) > 1200 else "")
        return _compact_instant_response(out, q) if want else out

    if related:
        rel_lines = [_clip_first_sentence(t, 110) for t in related[:5] if t]
        if not rel_lines:
            return None
        head = (
            "Quick answer (not one official ranking):\n"
            if want
            else "Quick answer:\n"
        )
        return head + "\n".join(f"- {x}" for x in rel_lines)

    results = data.get("Results") or []
    res_lines: list[str] = []
    for it in results[:6]:
        if isinstance(it, dict):
            t = (it.get("Text") or it.get("Title") or "").strip()
            if t:
                res_lines.append(_clip_first_sentence(t, 115))
    if res_lines:
        head = (
            "Quick answer (not one official ranking):\n"
            if want
            else "Quick answer:\n"
        )
        return head + "\n".join(f"- {x}" for x in res_lines[:5])

    return None


def snippet_answer(query: str) -> str:
    q = (query or "").strip()
    if not q:
        return "What should I search for?"

    g = _google_custom_search(q)
    if g:
        return _format_results(g, q)

    for qv in _search_query_variants(q):
        d = _duckduckgo_text_search(qv)
        if d:
            return _format_results(d, q)
        time.sleep(0.15)
        instant = _duckduckgo_instant_answer(qv)
        if instant:
            return instant
        time.sleep(0.12)

    wiki = _wikipedia_snippet(q)
    if wiki:
        return wiki

    if settings.google_search_api_key and not settings.google_cse_id:
        return (
            "Google Search API key is set but GOOGLE_CSE_ID is missing. "
            "Create a Programmable Search Engine and add the Search engine ID to .env."
        )
    if settings.google_cse_id and not settings.google_search_api_key:
        return "GOOGLE_CSE_ID is set but GOOGLE_SEARCH_API_KEY is missing in .env."

    if settings.google_search_api_key and settings.google_cse_id:
        return (
            "I could not reach live web search just now (Google Custom Search may be blocked for your project, and "
            "DuckDuckGo timed out or rate-limited). Wait a minute and try again, or use the Search page in the app. "
            "You can remove GOOGLE_SEARCH_API_KEY from backend/.env to skip the failing Google call and rely on "
            "DuckDuckGo only."
        )

    return (
        "Web search is temporarily unavailable. Wait a few minutes and try again, or open the Search page. "
        "Optional: add Google Programmable Search keys to backend/.env when your Cloud project has API access."
    )
