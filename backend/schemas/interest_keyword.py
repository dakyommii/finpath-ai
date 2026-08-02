import uuid

from pydantic import BaseModel, ConfigDict, Field


class InterestKeywordInput(BaseModel):
    axis: str = Field(min_length=1)
    keyword: str = Field(min_length=1)


class InterestKeywordBulkCreate(BaseModel):
    user_id: uuid.UUID
    keywords: list[InterestKeywordInput] = Field(min_length=1)


class InterestKeywordRead(InterestKeywordInput):
    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
