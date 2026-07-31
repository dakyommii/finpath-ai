import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FinancialProfileBase(BaseModel):
    age: int = Field(gt=0, le=120)
    region: str = Field(min_length=1)
    job_status: str = Field(min_length=1)
    annual_income: int = Field(ge=0)
    marital_status: str = Field(min_length=1)
    housing_type: str = Field(min_length=1)
    liquid_assets: int = Field(ge=0)
    total_debt: Optional[int] = Field(default=None, ge=0)
    monthly_saving: int = Field(ge=0)
    credit_score_band: Optional[str] = None


class FinancialProfileCreate(FinancialProfileBase):
    user_id: uuid.UUID


class FinancialProfileRead(FinancialProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
