from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SkillToggle
from app.schemas import SkillOut
from app.services.intent_engine import SKILL_DEFS

router = APIRouter(prefix="/api/skills", tags=["skills"])


class SkillToggleIn(BaseModel):
    enabled: bool


def _ensure_rows(db: Session) -> None:
    for sid in SKILL_DEFS:
        exists = db.query(SkillToggle).filter(SkillToggle.skill_id == sid).first()
        if not exists:
            db.add(SkillToggle(skill_id=sid, enabled=True))


@router.get("", response_model=list[SkillOut])
def list_skills(db: Session = Depends(get_db)):
    _ensure_rows(db)
    db.commit()
    rows = {r.skill_id: r.enabled for r in db.query(SkillToggle).all()}
    out = []
    for sid, meta in SKILL_DEFS.items():
        out.append(
            SkillOut(
                id=sid,
                name=meta["name"],
                description=meta["description"],
                enabled=rows.get(sid, True),
            )
        )
    return out


@router.patch("/{skill_id}", response_model=SkillOut)
def toggle_skill(skill_id: str, body: SkillToggleIn, db: Session = Depends(get_db)):
    if skill_id not in SKILL_DEFS:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Unknown skill")
    _ensure_rows(db)
    row = db.query(SkillToggle).filter(SkillToggle.skill_id == skill_id).first()
    if not row:
        row = SkillToggle(skill_id=skill_id, enabled=body.enabled)
        db.add(row)
    else:
        row.enabled = body.enabled
    db.commit()
    db.refresh(row)
    meta = SKILL_DEFS[skill_id]
    return SkillOut(
        id=skill_id,
        name=meta["name"],
        description=meta["description"],
        enabled=row.enabled,
    )
