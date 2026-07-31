from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.db import get_db
from models import FinancialGoal, FinancialProfile, LifeEvent
from schemas.recommendation import (
    RecommendationGenerateRequest,
    RecommendationItem,
    RecommendationResponse,
)
from services.scoring_service import score_and_rank

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.post("/generate", response_model=RecommendationResponse)
def generate_recommendations(payload: RecommendationGenerateRequest, db: Session = Depends(get_db)):
    profile = (
        db.query(FinancialProfile)
        .filter(FinancialProfile.user_id == payload.user_id)
        .first()
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="financial profile not found for user")

    goals = db.query(FinancialGoal).filter(FinancialGoal.user_id == payload.user_id).all()
    life_events = db.query(LifeEvent).filter(LifeEvent.user_id == payload.user_id).all()

    ranked = score_and_rank(db, profile, goals, life_events)

    items = [
        RecommendationItem(
            item_type=r.item_type,
            item_id=r.item_id,
            title=r.title,
            category=r.category,
            eligibility_status=r.eligibility_status.value,
            eligibility_factors=r.eligibility_factors,
            priority_score=round(r.priority_score * 100),
            reason=r.reason,
            benefit_info=r.benefit_info,
            application_end=r.application_end,
            official_url=r.official_url,
        )
        for r in ranked
    ]
    return RecommendationResponse(items=items)
