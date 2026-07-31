import uuid

from sqlalchemy import Column, String, Text, Date, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID

from core.db import Base


class Policy(Base):
    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    eligibility_rules = Column(JSONB, nullable=False, default=dict)
    benefit_info = Column(JSONB, nullable=True)
    application_start = Column(Date, nullable=True)
    application_end = Column(Date, nullable=True)
    official_url = Column(Text, nullable=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
