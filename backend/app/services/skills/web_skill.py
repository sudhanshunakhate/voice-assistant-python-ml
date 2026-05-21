from app.services.search_snippets import snippet_answer


def _strip_lookup_prefixes(text: str) -> str:
    q = text.strip()
    low = q.lower()
    for prefix in (
        "who is ",
        "what is ",
        "what are ",
        "tell me about ",
        "search for ",
        "look up ",
        "google ",
        "search ",
        "wikipedia ",
        "find ",
        "why is ",
        "where is ",
        "how does ",
        "how do ",
        "define ",
    ):
        if low.startswith(prefix):
            q = q[len(prefix) :].strip()
            low = q.lower()
            break
    return q


def search_web(command: str) -> str:
    q = _strip_lookup_prefixes(command)
    if not q:
        return "What would you like me to look up?"
    return snippet_answer(q)


def matches(text: str) -> bool:
    t = text.lower()
    return (
        "who is" in t
        or "what is" in t
        or "what are" in t
        or "tell me about" in t
        or t.startswith("wikipedia")
        or "search wikipedia" in t
        or "search for" in t
        or "look up" in t
        or t.startswith("google ")
        or t.startswith("find ")
        or "why is" in t
        or "where is" in t
        or "how does" in t
        or t.startswith("how do ")
        or t.startswith("define ")
    )


# Backwards-compatible name for any old references
def search_wikipedia(command: str) -> str:
    return search_web(command)
