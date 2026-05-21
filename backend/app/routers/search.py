from fastapi import APIRouter, Query

from app.config import settings
from app.services.search_snippets import snippet_answer

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/answer")
def get_search_answer(q: str = Query("", min_length=1, max_length=600)):
    """Short answer from Google CSE (if configured) or DuckDuckGo — same pipeline as web skill."""
    return {"answer": snippet_answer(q.strip())}


@router.get("/status")
def get_search_status():
    return {
        "google_custom_search_configured": bool(
            settings.google_search_api_key and settings.google_cse_id
        ),
    }
