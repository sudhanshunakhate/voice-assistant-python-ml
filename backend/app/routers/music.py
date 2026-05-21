import os
import shutil
from pathlib import Path

from pydantic import BaseModel

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import MUSIC_DIR
from app.database import get_db
from app.models import MusicTrack, Playlist, PlaylistItem
from app.schemas import MusicTrackOut, PlaylistOut

router = APIRouter(prefix="/api/music", tags=["music"])

ALLOWED_EXT = {".mp3", ".wav", ".ogg", ".m4a", ".webm"}


def _track_url(track_id: int, file_name: str) -> str:
    return f"/api/music/stream/{track_id}"


@router.get("/tracks", response_model=list[MusicTrackOut])
def list_tracks(db: Session = Depends(get_db)):
    rows = db.query(MusicTrack).order_by(MusicTrack.id.asc()).all()
    return [
        MusicTrackOut(
            id=r.id,
            title=r.title,
            artist=r.artist,
            file_name=r.file_name,
            url=_track_url(r.id, r.file_name),
            duration_seconds=r.duration_seconds,
            created_at=r.created_at,
        )
        for r in rows
    ]


class PlaylistCreate(BaseModel):
    name: str


@router.post("/tracks", response_model=MusicTrackOut)
async def upload_track(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    artist: str | None = Form(None),
    db: Session = Depends(get_db),
):
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename")
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"Unsupported type {ext}")

    safe_name = f"{os.urandom(8).hex()}{ext}"
    dest = MUSIC_DIR / safe_name
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    base_title = title or Path(file.filename).stem
    tr = MusicTrack(
        title=base_title,
        artist=artist or "Unknown",
        file_name=safe_name,
        duration_seconds=None,
    )
    db.add(tr)
    db.commit()
    db.refresh(tr)
    return MusicTrackOut(
        id=tr.id,
        title=tr.title,
        artist=tr.artist,
        file_name=tr.file_name,
        url=_track_url(tr.id, tr.file_name),
        duration_seconds=tr.duration_seconds,
        created_at=tr.created_at,
    )


@router.get("/stream/{track_id}")
def stream_track(track_id: int, db: Session = Depends(get_db)):
    tr = db.query(MusicTrack).filter(MusicTrack.id == track_id).first()
    if not tr:
        raise HTTPException(status_code=404, detail="Track not found")
    path = MUSIC_DIR / tr.file_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File missing")
    return FileResponse(
        path,
        filename=tr.file_name,
        media_type="audio/mpeg" if path.suffix.lower() == ".mp3" else "audio/*",
    )


@router.delete("/tracks/{track_id}")
def delete_track(track_id: int, db: Session = Depends(get_db)):
    tr = db.query(MusicTrack).filter(MusicTrack.id == track_id).first()
    if not tr:
        raise HTTPException(status_code=404, detail="Track not found")
    path = MUSIC_DIR / tr.file_name
    db.query(PlaylistItem).filter(PlaylistItem.track_id == track_id).delete()
    db.delete(tr)
    db.commit()
    if path.is_file():
        path.unlink()
    return {"ok": True}


@router.get("/playlists", response_model=list[PlaylistOut])
def list_playlists(db: Session = Depends(get_db)):
    playlists = db.query(Playlist).order_by(Playlist.id.asc()).all()
    out = []
    for p in playlists:
        items = (
            db.query(PlaylistItem)
            .filter(PlaylistItem.playlist_id == p.id)
            .order_by(PlaylistItem.position.asc())
            .all()
        )
        out.append(
            PlaylistOut(id=p.id, name=p.name, track_ids=[i.track_id for i in items])
        )
    return out


@router.post("/playlists", response_model=PlaylistOut)
def create_playlist(body: PlaylistCreate, db: Session = Depends(get_db)):
    p = Playlist(name=body.name.strip())
    if not p.name:
        raise HTTPException(status_code=400, detail="Name required")
    db.add(p)
    db.commit()
    db.refresh(p)
    return PlaylistOut(id=p.id, name=p.name, track_ids=[])
