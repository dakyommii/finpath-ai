import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.db import get_db
from models import FinancialGoal, FinancialProfile, InterestKeyword, LifeEvent, Roadmap
from repositories.roadmap_repository import save_roadmap
from schemas.roadmap import RoadmapDetailResponse, RoadmapGenerateRequest, RoadmapGoalInfo
from services.roadmap_service import enrich_steps_with_explanations, generate_roadmap_steps

router = APIRouter(prefix="/api/v1/roadmaps", tags=["roadmaps"])


def _primary_goal(goals: list[FinancialGoal]) -> Optional[FinancialGoal]:
    if not goals:
        return None
    return sorted(goals, key=lambda g: (g.priority is None, g.priority or 0))[0]


def _to_response(roadmap: Roadmap, goal: Optional[FinancialGoal]) -> RoadmapDetailResponse:
    goal_info = (
        RoadmapGoalInfo(type=goal.goal_type, target_amount=goal.target_amount, target_date=goal.target_date)
        if goal
        else None
    )
    return RoadmapDetailResponse(
        roadmap_id=roadmap.id,
        goal=goal_info,
        current_stage=roadmap.current_stage,
        progress=roadmap.progress,
        estimated_completion_date=roadmap.estimated_completion_date,
        steps=roadmap.steps,
    )


@router.post("/generate", response_model=RoadmapDetailResponse, status_code=201)
def generate_roadmap(payload: RoadmapGenerateRequest, db: Session = Depends(get_db)):
    profile = (
        db.query(FinancialProfile).filter(FinancialProfile.user_id == payload.user_id).first()
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="financial profile not found for user")

    goals = db.query(FinancialGoal).filter(FinancialGoal.user_id == payload.user_id).all()
    life_events = db.query(LifeEvent).filter(LifeEvent.user_id == payload.user_id).all()
    keywords = [
        k.keyword
        for k in db.query(InterestKeyword).filter(InterestKeyword.user_id == payload.user_id).all()
    ]

    steps = generate_roadmap_steps(db, profile, goals, life_events, keywords)
    enrich_steps_with_explanations(db, steps)
    primary_goal = _primary_goal(goals)
    roadmap = save_roadmap(db, payload.user_id, primary_goal.id if primary_goal else None, steps)

    return _to_response(roadmap, primary_goal)


@router.get("/{roadmap_id}", response_model=RoadmapDetailResponse)
def get_roadmap(roadmap_id: uuid.UUID, db: Session = Depends(get_db)):
    roadmap = db.get(Roadmap, roadmap_id)
    if roadmap is None:
        raise HTTPException(status_code=404, detail="roadmap not found")

    goal = db.get(FinancialGoal, roadmap.goal_id) if roadmap.goal_id else None
    return _to_response(roadmap, goal)
