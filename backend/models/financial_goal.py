import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, BigInteger, Date
from sqlalchemy.dialects.postgresql import UUID

from core.db import Base


class FinancialGoal(Base):
    __tablename__ = "financial_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    goal_type = Column(String, nullable=False)
    target_amount = Column(BigInteger, nullable=True)
    target_date = Column(Date, nullable=True)
    priority = Column(Integer, nullable=True)
