import uuid
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class PolicyBase(BaseModel):
    title: str
    category: str
    description: Optional[str] = None
    eligibility_rules: dict[str, Any]
    benefit_info: Optional[dict[str, Any]] = None
    application_start: Optional[date] = None
    application_end: Optional[date] = None
    official_url: Optional[str] = None
    last_verified_at: Optional[datetime] = None


class PolicyCreate(PolicyBase):
    pass


class PolicyRead(PolicyBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
