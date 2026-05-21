from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ConversationMessage
from app.schemas import CommandIn, CommandOut
from app.services.intent_engine import process_command

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.post("/command", response_model=CommandOut)
def post_command(body: CommandIn, db: Session = Depends(get_db)):
    result = process_command(body.text, db, skip_wake_check=body.skip_wake_check)

    db.add(
        ConversationMessage(
            role="user",
            content=body.text.strip(),
            intent=None,
        )
    )
    db.add(
        ConversationMessage(
            role="assistant",
            content=result["response"],
            intent=result.get("intent"),
        )
    )
    db.commit()

    return CommandOut(
        response=result["response"],
        intent=result["intent"],
        action=result.get("action"),
        payload=result.get("payload"),
    )
