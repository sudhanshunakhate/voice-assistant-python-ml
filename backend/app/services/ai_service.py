import httpx

from app.config import settings
from app.services.search_snippets import snippet_answer

_SYSTEM = (
    "You are S.U.K.U, a helpful voice companion. Keep answers concise for spoken responses "
    "(under 120 words unless the user asks for lists or detail)."
)


def _answer_from_gemini(user_message: str, system_prompt: str) -> str:
    key = settings.gemini_api_key
    if not key:
        raise ValueError("no gemini key")

    model = settings.gemini_model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "contents": [{"parts": [{"text": user_message.strip()}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {
            "maxOutputTokens": 700,
            "temperature": 0.7,
        },
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(url, params={"key": key}, json=body)
        if r.status_code == 404 and model != "gemini-1.5-flash":
            url_fb = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
            r = client.post(url_fb, params={"key": key}, json=body)
        r.raise_for_status()
        data = r.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts).strip()
    except (KeyError, IndexError) as e:
        return f"Google returned an unexpected response ({e}). Try again or use web search."
    if not text:
        return snippet_answer(user_message)
    return text


def _answer_from_openai(user_message: str, system_prompt: str) -> str:
    if not settings.openai_api_key:
        raise ValueError("no openai key")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message.strip()},
        ],
        "max_tokens": 500,
        "temperature": 0.7,
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(url, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
    return data["choices"][0]["message"]["content"].strip()


def chat_completion_sync(user_message: str, system_prompt: str | None = None) -> str:
    sys = system_prompt or _SYSTEM
    msg = user_message.strip()
    if not msg:
        return "What would you like to know?"

    if settings.gemini_api_key:
        try:
            return _answer_from_gemini(msg, sys)
        except Exception:
            pass

    if settings.openai_api_key:
        try:
            return _answer_from_openai(msg, sys)
        except Exception:
            pass

    return snippet_answer(msg)


async def chat_completion(user_message: str, system_prompt: str | None = None) -> str:
    return chat_completion_sync(user_message, system_prompt)
