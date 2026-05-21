from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Reminder
from app.schemas import ReminderOut

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.get("", response_model=list[ReminderOut])
def list_reminders_api(db: Session = Depends(get_db)):
    return (
        db.query(Reminder)
        .filter(Reminder.dismissed.is_(False))
        .filter(Reminder.fire_at >= datetime.now())
        .order_by(Reminder.fire_at.asc())
        .all()
    )


@router.delete("/{reminder_id}")
def dismiss_reminder(reminder_id: int, db: Session = Depends(get_db)):
    row = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    row.dismissed = True
    db.commit()
    return {"ok": True}
