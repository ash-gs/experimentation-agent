"""SQLAlchemy database models."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .schemas import (
    DecisionRecommendation,
    Direction,
    ExperimentPhase,
    ExperimentStatus,
    MetricType,
    RandomizationUnit,
)


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Experiment(Base):
    """Experiment model."""

    __tablename__ = "experiments"

    experiment_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phase: Mapped[ExperimentPhase] = mapped_column(
        Enum(ExperimentPhase), default=ExperimentPhase.HYPOTHESIS
    )
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus), default=ExperimentStatus.DRAFT
    )

    # Hypothesis data
    hypothesis_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    hypothesis_metric: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hypothesis_direction: Mapped[Direction | None] = mapped_column(Enum(Direction), nullable=True)
    hypothesis_effect_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    hypothesis_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Design configuration
    design_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sample_size_per_variant: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power: Mapped[float | None] = mapped_column(Float, nullable=True)
    significance_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    minimum_detectable_effect: Mapped[float | None] = mapped_column(Float, nullable=True)
    randomization_unit: Mapped[RandomizationUnit | None] = mapped_column(
        Enum(RandomizationUnit), nullable=True
    )
    traffic_allocation: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Analysis results
    analysis_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Decision
    decision_recommendation: Mapped[DecisionRecommendation | None] = mapped_column(
        Enum(DecisionRecommendation), nullable=True
    )
    decision_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Metadata
    conversation_history: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    variants: Mapped[list["Variant"]] = relationship(
        "Variant", back_populates="experiment", cascade="all, delete-orphan"
    )
    events: Mapped[list["UserEvent"]] = relationship(
        "UserEvent", back_populates="experiment", cascade="all, delete-orphan"
    )


class Variant(Base):
    """Experiment variant model."""

    __tablename__ = "variants"

    variant_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    experiment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("experiments.experiment_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    allocation_percent: Mapped[float] = mapped_column(Float, nullable=False)
    is_control: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="variants")
    events: Mapped[list["UserEvent"]] = relationship("UserEvent", back_populates="variant")


class UserEvent(Base):
    """User event model for experiment data."""

    __tablename__ = "user_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    experiment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("experiments.experiment_id"), nullable=False, index=True
    )
    variant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("variants.variant_id"), nullable=False, index=True
    )
    variant_name: Mapped[str] = mapped_column(String(100), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    metric_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    properties: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="events")
    variant: Mapped["Variant"] = relationship("Variant", back_populates="events")


class MetricDefinition(Base):
    """Metric definition model."""

    __tablename__ = "metric_definitions"

    metric_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    metric_type: Mapped[MetricType] = mapped_column(Enum(MetricType), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_guardrail: Mapped[bool] = mapped_column(Boolean, default=False)
    expected_direction: Mapped[Direction | None] = mapped_column(Enum(Direction), nullable=True)
    calculation_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
