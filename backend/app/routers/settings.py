from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings as app_settings
from app.database import get_db
from app.models import AppSetting
from app.schemas import SettingItem, SettingsOut, SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_setting(db: Session, key: str, default: str = "") -> str:
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    return row.value if row and row.value is not None else default


def _set_setting(db: Session, key: str, value: str) -> None:
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if row:
        row.value = value
    else:
        db.add(AppSetting(key=key, value=value))


@router.get("", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db)):
    wake = _get_setting(db, "wake_word", app_settings.wake_word_default)
    try:
        voice_rate = int(_get_setting(db, "voice_rate", "1"))
    except ValueError:
        voice_rate = 1
    all_rows = db.query(AppSetting).all()
    items = [SettingItem(key=r.key, value=r.value) for r in all_rows]
    return SettingsOut(wake_word=wake, voice_rate=voice_rate, items=items)


@router.put("", response_model=SettingsOut)
def update_settings(body: SettingsUpdate, db: Session = Depends(get_db)):
    if body.wake_word is not None:
        w = body.wake_word.strip()
        if w:
            _set_setting(db, "wake_word", w)
    if body.voice_rate is not None:
        _set_setting(db, "voice_rate", str(max(0, min(2, body.voice_rate))))
    db.commit()
    return get_settings(db)
