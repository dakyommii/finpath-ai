import uuid
from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.db import get_db
from models import FinancialGoal, FinancialProfile, LifeEvent, Roadmap
from schemas.simulation import SimulationRequest, SimulationResponse, SimulationStepSummarySchema
from services.simulation_service import simulate_roadmap

router = APIRouter(prefix="/api/v1/roadmaps", tags=["simulations"])


def _to_step_schema(step_summary) -> SimulationStepSummarySchema:
    return SimulationStepSummarySchema(
        title=step_summary.title,
        status=step_summary.status,
        recommended_start=step_summary.recommended_start,
        expected_end=step_summary.expected_end,
    )


@router.post("/{roadmap_id}/simulate", response_model=SimulationResponse)
def simulate(roadmap_id: uuid.UUID, payload: SimulationRequest, db: Session = Depends(get_db)):
    roadmap = db.get(Roadmap, roadmap_id)
    if roadmap is None:
        raise HTTPException(status_code=404, detail="roadmap not found")

    profile = (
        db.query(FinancialProfile).filter(FinancialProfile.user_id == roadmap.user_id).first()
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="financial profile not found for roadmap owner")

    goals = db.query(FinancialGoal).filter(FinancialGoal.user_id == roadmap.user_id).all()
    life_events = db.query(LifeEvent).filter(LifeEvent.user_id == roadmap.user_id).all()
    extra_life_events = [SimpleNamespace(event_type=e.event_type) for e in (payload.life_events or [])]

    result = simulate_roadmap(
        db,
        roadmap,
        profile,
        goals,
        life_events,
        monthly_saving=payload.monthly_saving,
        annual_income=payload.annual_income,
        extra_life_events=extra_life_events,
    )
    return SimulationResponse(
        original_estimated_completion_date=result.original_estimated_completion_date,
        simulated_estimated_completion_date=result.simulated_estimated_completion_date,
        months_saved=result.months_saved,
        added_steps=result.added_steps,
        removed_steps=result.removed_steps,
        original_steps=[_to_step_schema(s) for s in result.original_steps],
        simulated_steps=[_to_step_schema(s) for s in result.simulated_steps],
    )
