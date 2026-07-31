from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.db import get_db
from models import FinancialGoal, User
from schemas.financial_goal import FinancialGoalCreate, FinancialGoalRead

router = APIRouter(prefix="/api/v1/goals", tags=["goals"])


@router.post("", response_model=FinancialGoalRead, status_code=201)
def create_goal(payload: FinancialGoalCreate, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")

    goal = FinancialGoal(**payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal
