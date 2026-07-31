import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class FinancialProductBase(BaseModel):
    provider: str
    title: str
    category: str
    product_rules: dict[str, Any]
    rate_info: Optional[dict[str, Any]] = None
    benefit_info: Optional[dict[str, Any]] = None
    official_url: Optional[str] = None
    last_verified_at: Optional[datetime] = None


class FinancialProductCreate(FinancialProductBase):
    pass


class FinancialProductRead(FinancialProductBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
