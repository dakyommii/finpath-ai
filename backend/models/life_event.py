import uuid

from sqlalchemy import Column, ForeignKey, String, Date
from sqlalchemy.dialects.postgresql import UUID

from core.db import Base


class LifeEvent(Base):
    __tablename__ = "life_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    event_type = Column(String, nullable=False)
    expected_date = Column(Date, nullable=True)
    certainty = Column(String, nullable=True)
