from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import MUSIC_DIR, settings
from app.database import init_db
from app.routers import assistant, history, music, reminders, search, settings as settings_router, skills, system, youtube


@asynccontextmanager
async def lifespan(app: FastAPI):
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(assistant.router)
app.include_router(history.router)
app.include_router(music.router)
app.include_router(settings_router.router)
app.include_router(skills.router)
app.include_router(reminders.router)
app.include_router(system.router)
app.include_router(youtube.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}
