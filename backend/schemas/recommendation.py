import uuid
from datetime import date
from typing import Any, Optional

from pydantic import BaseModel


class RecommendationGenerateRequest(BaseModel):
    user_id: uuid.UUID


class RecommendationItem(BaseModel):
    item_type: str
    item_id: str
    title: str
    category: str
    eligibility_status: str
    eligibility_factors: dict[str, str]
    priority_score: int
    reason: str
    benefit_info: Optional[dict[str, Any]] = None
    application_end: Optional[date] = None
    official_url: Optional[str] = None


class RecommendationResponse(BaseModel):
    items: list[RecommendationItem]
