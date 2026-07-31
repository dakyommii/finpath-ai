from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.db import get_db
from models import FinancialProfile, User
from schemas.financial_profile import FinancialProfileBase, FinancialProfileRead

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])


@router.post("", response_model=FinancialProfileRead, status_code=201)
def create_profile(payload: FinancialProfileBase, db: Session = Depends(get_db)):
    user = User()
    db.add(user)
    db.flush()

    profile = FinancialProfile(user_id=user.id, **payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
