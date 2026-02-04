"""Pydantic schemas for type-safe data structures."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# Enums

class ExperimentPhase(str, Enum):
    """Experiment lifecycle phases."""

    HYPOTHESIS = "hypothesis"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    RUNNING = "running"
    ANALYSIS = "analysis"
    DECISION = "decision"
    COMPLETE = "complete"


class ExperimentStatus(str, Enum):
    """Experiment execution status."""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Direction(str, Enum):
    """Expected direction of metric change."""

    INCREASE = "increase"
    DECREASE = "decrease"
    NEUTRAL = "neutral"


class DecisionRecommendation(str, Enum):
    """Experiment decision recommendations."""

    SHIP = "ship"
    NO_SHIP = "no_ship"
    ITERATE = "iterate"
    INCONCLUSIVE = "inconclusive"


class MetricType(str, Enum):
    """Type of metric."""

    BINARY = "binary"  # Conversion rate, click-through rate
    CONTINUOUS = "continuous"  # Revenue, time on site
    COUNT = "count"  # Number of actions
    RATIO = "ratio"  # Ratio of two metrics


class RandomizationUnit(str, Enum):
    """Unit for randomization."""

    USER = "user"
    SESSION = "session"
    REQUEST = "request"


# Schemas

class HypothesisSchema(BaseModel):
    """Hypothesis schema for experiment."""

    description: str = Field(..., description="Natural language hypothesis description")
    metric: str = Field(..., description="Primary metric to measure")
    expected_direction: Direction = Field(..., description="Expected direction of change")
    expected_effect_size: float = Field(..., description="Expected effect size (absolute)")
    rationale: str | None = Field(None, description="Reasoning behind the hypothesis")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VariantSchema(BaseModel):
    """Variant configuration schema."""

    variant_id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Variant name (e.g., 'control', 'treatment')")
    description: str = Field(..., description="What this variant changes")
    allocation_percent: float = Field(..., description="Traffic allocation percentage", ge=0, le=100)
    is_control: bool = Field(default=False, description="Whether this is the control variant")


class DesignConfigSchema(BaseModel):
    """Experiment design configuration."""

    variants: list[VariantSchema] = Field(..., description="List of variants")
    sample_size_per_variant: int = Field(..., description="Required sample size per variant", gt=0)
    duration_days: int = Field(..., description="Expected experiment duration in days", gt=0)
    power: float = Field(default=0.8, description="Statistical power (1 - β)", ge=0, le=1)
    significance_level: float = Field(default=0.05, description="Significance level (α)", ge=0, le=1)
    minimum_detectable_effect: float = Field(
        ..., description="Minimum detectable effect (MDE)"
    )
    randomization_unit: RandomizationUnit = Field(
        default=RandomizationUnit.USER, description="Unit of randomization"
    )
    traffic_allocation: float = Field(
        default=1.0, description="Proportion of traffic to include", ge=0, le=1
    )


class MetricDefinitionSchema(BaseModel):
    """Metric definition schema."""

    metric_id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Metric name")
    metric_type: MetricType = Field(..., description="Type of metric")
    is_primary: bool = Field(default=False, description="Whether this is the primary metric")
    is_guardrail: bool = Field(default=False, description="Whether this is a guardrail metric")
    expected_direction: Direction | None = Field(None, description="Expected direction")
    calculation_description: str | None = Field(None, description="How the metric is calculated")


class StatisticalTestResultSchema(BaseModel):
    """Statistical test result schema."""

    test_type: str = Field(..., description="Type of statistical test performed")
    control_mean: float = Field(..., description="Control variant mean")
    treatment_mean: float = Field(..., description="Treatment variant mean")
    control_std: float | None = Field(None, description="Control variant standard deviation")
    treatment_std: float | None = Field(None, description="Treatment variant standard deviation")
    control_n: int = Field(..., description="Control sample size")
    treatment_n: int = Field(..., description="Treatment sample size")
    statistic: float = Field(..., description="Test statistic value")
    p_value: float = Field(..., description="P-value", ge=0, le=1)
    confidence_interval_lower: float = Field(..., description="Lower bound of CI")
    confidence_interval_upper: float = Field(..., description="Upper bound of CI")
    confidence_level: float = Field(default=0.95, description="Confidence level", ge=0, le=1)
    effect_size: float = Field(..., description="Absolute effect size")
    relative_effect: float | None = Field(None, description="Relative effect (percentage)")
    statistically_significant: bool = Field(..., description="Whether result is significant")
    practical_significance: bool | None = Field(
        None, description="Whether result is practically significant"
    )


class AnalysisResultSchema(BaseModel):
    """Complete analysis result for an experiment."""

    analysis_id: UUID = Field(default_factory=uuid4)
    experiment_id: UUID = Field(..., description="Associated experiment ID")
    primary_metric_result: StatisticalTestResultSchema = Field(
        ..., description="Primary metric test result"
    )
    secondary_metrics: list[StatisticalTestResultSchema] | None = Field(
        None, description="Secondary metric results"
    )
    guardrail_violations: list[str] | None = Field(
        None, description="List of guardrail violations"
    )
    sample_ratio_mismatch: bool = Field(
        default=False, description="Whether SRM was detected"
    )
    data_quality_issues: list[str] | None = Field(
        None, description="Data quality issues found"
    )
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    interpretation: str | None = Field(None, description="Human-readable interpretation")


class DecisionSchema(BaseModel):
    """Experiment decision schema."""

    decision_id: UUID = Field(default_factory=uuid4)
    recommendation: DecisionRecommendation = Field(..., description="Decision recommendation")
    rationale: str = Field(..., description="Reasoning behind the decision")
    confidence: float = Field(..., description="Confidence in decision", ge=0, le=1)
    key_findings: list[str] = Field(default_factory=list, description="Key findings summary")
    next_steps: list[str] = Field(default_factory=list, description="Recommended next steps")
    risks: list[str] | None = Field(None, description="Identified risks")
    decision_timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExperimentStateSchema(BaseModel):
    """Complete experiment state through lifecycle."""

    experiment_id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Experiment name")
    phase: ExperimentPhase = Field(
        default=ExperimentPhase.HYPOTHESIS, description="Current lifecycle phase"
    )
    status: ExperimentStatus = Field(
        default=ExperimentStatus.DRAFT, description="Execution status"
    )

    # Lifecycle data
    hypothesis: HypothesisSchema | None = None
    design: DesignConfigSchema | None = None
    analysis: AnalysisResultSchema | None = None
    decision: DecisionSchema | None = None

    # Metadata
    conversation_history: list[dict[str, Any]] = Field(
        default_factory=list, description="Conversation history"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str | None = Field(None, description="Creator identifier")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "experiment_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Button Color Test",
                "phase": "design",
                "status": "draft",
            }
        }


class UserEventSchema(BaseModel):
    """User event for synthetic data."""

    event_id: UUID = Field(default_factory=uuid4)
    user_id: str = Field(..., description="Hashed user identifier")
    session_id: str = Field(..., description="Session identifier")
    experiment_id: UUID = Field(..., description="Experiment ID")
    variant_id: UUID = Field(..., description="Assigned variant ID")
    variant_name: str = Field(..., description="Variant name")
    event_type: str = Field(..., description="Type of event (exposure, conversion, etc.)")
    event_timestamp: datetime = Field(default_factory=datetime.utcnow)
    metric_value: float | None = Field(None, description="Numeric value for metrics")
    properties: dict[str, Any] = Field(
        default_factory=dict, description="Additional event properties"
    )


class ExperimentDataSchema(BaseModel):
    """Complete experiment data including all events."""

    experiment: ExperimentStateSchema = Field(..., description="Experiment configuration")
    events: list[UserEventSchema] = Field(default_factory=list, description="User events")
    total_users: int = Field(..., description="Total unique users")
    total_events: int = Field(..., description="Total events")
    date_range_start: datetime = Field(..., description="Start of data collection")
    date_range_end: datetime = Field(..., description="End of data collection")
