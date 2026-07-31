from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class SimulationLifeEventInput(BaseModel):
    event_type: str = Field(min_length=1)
    expected_date: Optional[date] = None


class SimulationRequest(BaseModel):
    monthly_saving: Optional[int] = Field(default=None, ge=0)
    annual_income: Optional[int] = Field(default=None, ge=0)
    life_events: Optional[list[SimulationLifeEventInput]] = None


class SimulationStepSummarySchema(BaseModel):
    title: str
    status: str
    recommended_start: Optional[date] = None
    expected_end: Optional[date] = None


class SimulationResponse(BaseModel):
    original_estimated_completion_date: Optional[date] = None
    simulated_estimated_completion_date: Optional[date] = None
    months_saved: Optional[int] = None
    added_steps: list[str]
    removed_steps: list[str]
    original_steps: list[SimulationStepSummarySchema]
    simulated_steps: list[SimulationStepSummarySchema]
