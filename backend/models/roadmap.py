import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, Text, Date, DateTime, Float, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from core.db import Base


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("financial_goals.id"), nullable=True)
    current_stage = Column(String, nullable=True)
    progress = Column(Float, nullable=True)
    estimated_completion_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    steps = relationship(
        "RoadmapStep", back_populates="roadmap", order_by="RoadmapStep.step_order"
    )


class RoadmapStep(Base):
    __tablename__ = "roadmap_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roadmap_id = Column(UUID(as_uuid=True), ForeignKey("roadmaps.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False)
    recommended_start = Column(Date, nullable=True)
    expected_end = Column(Date, nullable=True)
    action = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    expected_benefit = Column(JSONB, nullable=True)
    completion_condition = Column(Text, nullable=True)
    related_items = Column(JSONB, nullable=True, default=list)
    sources = Column(JSONB, nullable=True, default=list)

    roadmap = relationship("Roadmap", back_populates="steps")
