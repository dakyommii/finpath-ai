import uuid

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from core.db import Base


class InterestKeyword(Base):
    __tablename__ = "interest_keywords"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    axis = Column(String, nullable=False)
    keyword = Column(String, nullable=False)
