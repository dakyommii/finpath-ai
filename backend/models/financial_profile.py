import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, BigInteger
from sqlalchemy.dialects.postgresql import UUID

from core.db import Base


class FinancialProfile(Base):
    __tablename__ = "financial_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    age = Column(Integer, nullable=False)
    region = Column(String, nullable=False)
    job_status = Column(String, nullable=False)
    annual_income = Column(BigInteger, nullable=False)
    marital_status = Column(String, nullable=False)
    housing_type = Column(String, nullable=False)
    liquid_assets = Column(BigInteger, nullable=False)
    total_debt = Column(BigInteger, nullable=True)
    monthly_saving = Column(BigInteger, nullable=False)
    credit_score_band = Column(String, nullable=True)
