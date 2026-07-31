from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.db import get_db
from models import LifeEvent, User
from schemas.life_event import LifeEventCreate, LifeEventRead

router = APIRouter(prefix="/api/v1/life-events", tags=["life-events"])


@router.post("", response_model=LifeEventRead, status_code=201)
def create_life_event(payload: LifeEventCreate, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")

    life_event = LifeEvent(**payload.model_dump())
    db.add(life_event)
    db.commit()
    db.refresh(life_event)
    return life_event
