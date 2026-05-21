from datetime import datetime

from pydantic import BaseModel, Field


class CommandIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    skip_wake_check: bool = False


class CommandOut(BaseModel):
    response: str
    intent: str
    action: str | None = None
    payload: dict | None = None


class SettingItem(BaseModel):
    key: str
    value: str


class SettingsOut(BaseModel):
    wake_word: str
    voice_rate: int = 1
    items: list[SettingItem] = []


class SettingsUpdate(BaseModel):
    wake_word: str | None = None
    voice_rate: int | None = None
    openai_enabled: bool | None = None


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    intent: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class SkillOut(BaseModel):
    id: str
    name: str
    description: str
    enabled: bool


class MusicTrackOut(BaseModel):
    id: int
    title: str
    artist: str
    file_name: str
    url: str
    duration_seconds: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class PlaylistOut(BaseModel):
    id: int
    name: str
    track_ids: list[int]


class ReminderOut(BaseModel):
    id: int
    label: str
    fire_at: datetime
    dismissed: bool
    created_at: datetime

    class Config:
        from_attributes = True
