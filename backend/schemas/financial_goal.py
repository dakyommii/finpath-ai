import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FinancialGoalBase(BaseModel):
    goal_type: str = Field(min_length=1)
    target_amount: Optional[int] = Field(default=None, ge=0)
    target_date: Optional[date] = None
    priority: Optional[int] = Field(default=None, ge=1)


class FinancialGoalCreate(FinancialGoalBase):
    user_id: uuid.UUID


class FinancialGoalRead(FinancialGoalBase):
    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
