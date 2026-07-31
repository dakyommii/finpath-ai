import uuid
from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class RoadmapStepBase(BaseModel):
    step_order: int
    title: str
    status: str
    recommended_start: Optional[date] = None
    expected_end: Optional[date] = None
    action: Optional[str] = None
    reason: Optional[str] = None
    expected_benefit: Optional[dict[str, Any]] = None
    completion_condition: Optional[str] = None
    related_items: Optional[list[Any]] = None
    sources: Optional[list[Any]] = None


class RoadmapStepRead(RoadmapStepBase):
    id: uuid.UUID
    roadmap_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class RoadmapBase(BaseModel):
    current_stage: Optional[str] = None
    progress: Optional[float] = None
    estimated_completion_date: Optional[date] = None


class RoadmapRead(RoadmapBase):
    id: uuid.UUID
    user_id: uuid.UUID
    goal_id: Optional[uuid.UUID] = None
    steps: list[RoadmapStepRead] = []

    model_config = ConfigDict(from_attributes=True)


class RoadmapGoalInfo(BaseModel):
    type: str
    target_amount: Optional[int] = None
    target_date: Optional[date] = None


class RoadmapGenerateRequest(BaseModel):
    user_id: uuid.UUID


class RoadmapDetailResponse(BaseModel):
    roadmap_id: uuid.UUID
    goal: Optional[RoadmapGoalInfo] = None
    current_stage: Optional[str] = None
    progress: Optional[float] = None
    estimated_completion_date: Optional[date] = None
    steps: list[RoadmapStepRead] = []
