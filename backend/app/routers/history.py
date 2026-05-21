from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ConversationMessage
from app.schemas import MessageOut

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=list[MessageOut])
def list_history(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    rows = (
        db.query(ConversationMessage)
        .order_by(ConversationMessage.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return list(reversed(rows))


@router.delete("")
def clear_history(db: Session = Depends(get_db)):
    db.query(ConversationMessage).delete()
    db.commit()
    return {"ok": True}
