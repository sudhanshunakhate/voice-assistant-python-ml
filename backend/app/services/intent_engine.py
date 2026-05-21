from sqlalchemy.orm import Session

from app.config import settings
from app.models import SkillToggle
from app.services.ai_service import chat_completion_sync
from app.services.skills import math_skill, music_skill, reminder_skill, system_skill, time_skill, web_skill

SKILL_DEFS = {
    "time": {"name": "Time & date", "description": "Current time and date"},
    "system": {"name": "System info", "description": "OS and device information"},
    "web": {"name": "Web search", "description": "Web snippets (Google if configured, else DuckDuckGo)"},
    "math": {
        "name": "Math",
        "description": "Arithmetic, algebra, calculus (SymPy) with short solution-method hints",
    },
    "music": {
        "name": "Music & YouTube",
        "description": "Play songs by voice (opens YouTube in a new tab); pause/stop for local player",
    },
    "reminder": {"name": "Reminders", "description": "Set and list reminders by time (no cloud required)"},
    "ai": {
        "name": "AI chat",
        "description": "Answers general questions (web snippets via Google CSE or DuckDuckGo; optional Gemini or OpenAI)",
    },
}


def _skill_enabled(db: Session, skill_id: str) -> bool:
    row = db.query(SkillToggle).filter(SkillToggle.skill_id == skill_id).first()
    if row is None:
        return True
    return row.enabled


def _get_wake_word(db: Session) -> str:
    from app.models import AppSetting

    row = db.query(AppSetting).filter(AppSetting.key == "wake_word").first()
    if row and row.value:
        return row.value.strip().lower()
    return settings.wake_word_default.lower()


def process_command(text: str, db: Session, skip_wake_check: bool = False) -> dict:
    raw = text.strip()
    lower = raw.lower()
    wake = _get_wake_word(db)

    if not skip_wake_check and wake and wake not in lower:
        return {
            "response": f"Say the wake word {wake!r} first, or use text mode on the dashboard.",
            "intent": "wake_required",
            "action": None,
            "payload": {"wake_word": wake},
        }

    command = raw
    if wake and wake in lower:
        idx = lower.find(wake)
        command = raw[idx + len(wake) :].strip(" ,.:-\t")
    if not command:
        return {
            "response": "Yes? What would you like me to do?",
            "intent": "empty",
            "action": None,
            "payload": None,
        }

    lower_cmd = command.lower()
    if any(x in lower_cmd for x in ("exit", "goodbye", "shut down", "stop listening")):
        return {
            "response": "Goodbye. Open the app anytime you need me.",
            "intent": "goodbye",
            "action": None,
            "payload": None,
        }

    if _skill_enabled(db, "music"):
        resp, intent, payload = music_skill.handle_music_intent(command, db)
        if intent == "music":
            return {"response": resp, "intent": intent, "action": payload.get("action") if payload else None, "payload": payload}

    if _skill_enabled(db, "time") and time_skill.matches(command):
        return {
            "response": time_skill.tell_time(),
            "intent": "time",
            "action": None,
            "payload": None,
        }

    if _skill_enabled(db, "system") and system_skill.matches(command):
        return {
            "response": system_skill.system_info(),
            "intent": "system",
            "action": None,
            "payload": None,
        }

    if _skill_enabled(db, "math") and math_skill.matches(command):
        return {
            "response": math_skill.solve_math(command),
            "intent": "math",
            "action": None,
            "payload": None,
        }

    if _skill_enabled(db, "web") and web_skill.matches(command):
        return {
            "response": web_skill.search_web(command),
            "intent": "web",
            "action": None,
            "payload": None,
        }

    if _skill_enabled(db, "reminder"):
        r_msg, r_intent, r_payload = reminder_skill.handle(db, command)
        if r_intent == "reminder":
            return {
                "response": r_msg,
                "intent": r_intent,
                "action": None,
                "payload": r_payload,
            }

    if _skill_enabled(db, "ai"):
        try:
            reply = chat_completion_sync(command)
        except Exception as e:
            reply = f"I could not reach the AI service: {e!s}"
        return {
            "response": reply,
            "intent": "ai",
            "action": None,
            "payload": None,
        }

    return {
        "response": (
            "I am not sure how to help with that. Try play music with a song name, time, "
            "reminders, math (e.g. calculate …, integrate …), web search, or a general question."
        ),
        "intent": "unknown",
        "action": None,
        "payload": None,
    }
