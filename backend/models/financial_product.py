import uuid

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID

from core.db import Base


class FinancialProduct(Base):
    __tablename__ = "financial_products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String, nullable=False)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    product_rules = Column(JSONB, nullable=False, default=dict)
    rate_info = Column(JSONB, nullable=True)
    benefit_info = Column(JSONB, nullable=True)
    official_url = Column(Text, nullable=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
