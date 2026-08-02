from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.db import get_db
from models import InterestKeyword, User
from schemas.interest_keyword import InterestKeywordBulkCreate, InterestKeywordRead

router = APIRouter(prefix="/api/v1/interest-keywords", tags=["interest-keywords"])


@router.post("", response_model=list[InterestKeywordRead], status_code=201)
def create_interest_keywords(payload: InterestKeywordBulkCreate, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")

    records = [
        InterestKeyword(user_id=payload.user_id, axis=item.axis, keyword=item.keyword)
        for item in payload.keywords
    ]
    db.add_all(records)
    db.commit()
    for record in records:
        db.refresh(record)
    return records
