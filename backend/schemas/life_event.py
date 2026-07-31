import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LifeEventBase(BaseModel):
    event_type: str = Field(min_length=1)
    expected_date: Optional[date] = None
    certainty: Optional[str] = None


class LifeEventCreate(LifeEventBase):
    user_id: uuid.UUID


class LifeEventRead(LifeEventBase):
    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
