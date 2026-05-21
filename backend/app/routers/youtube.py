from fastapi import APIRouter, Query

from app.services.youtube_client import search_videos

router = APIRouter(prefix="/api/youtube", tags=["youtube"])


@router.get("/search")
def youtube_search(q: str = Query(..., min_length=1, max_length=300), limit: int = Query(5, ge=1, le=15)):
    hits = search_videos(q, limit)
    return hits
