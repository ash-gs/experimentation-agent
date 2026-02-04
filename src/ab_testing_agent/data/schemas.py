"""Pydantic schemas for AB Testing Agent data models."""

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Direction(str, Enum):
    """Direction of expected effect."""

    INCREASE = "increase"
    DECREASE = "decrease"
    BOTH = "both"


class MetricType(str, Enum):
    """Type of metric being measured."""

    CONVERSION_RATE = "conversion_rate"
    CONTINUOUS = "continuous"
    RATIO = "ratio"
    BINARY = "binary"


class RandomizationUnit(str, Enum):
    """Unit of randomization for experiment."""

    USER = "user"
    SESSION = "session"
    DEVICE = "device"
    IP = "ip"


class DecisionRecommendation(str, Enum):
    """Decision recommendation for experiment."""

    SHIP = "ship"
    NO_SHIP = "no_ship"
    ITERATE = "iterate"
    INCONCLUSIVE = "inconclusive"


# ============================================================================
# Hypothesis Phase Schemas
# ============================================================================


class HypothesisSchema(BaseModel):
    """Schema for an AB test hypothesis."""

    description: str = Field(..., description="Human-readable hypothesis description")
    metric: str = Field(..., description="Primary metric to measure")
    expected_direction: Direction = Field(..., description="Expected direction of effect")
    expected_effect_size: float = Field(..., description="Expected effect size (e.g., 0.05 for 5%)")
    rationale: str = Field(..., description="Rationale for the hypothesis")
    is_testable: bool = Field(default=True, description="Whether hypothesis is testable")
    is_specific: bool = Field(default=True, description="Whether hypothesis is specific")
    is_measurable: bool = Field(default=True, description="Whether hypothesis is measurable")
    tags: list[str] = Field(default_factory=list, description="Tags for organizing hypotheses")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# ============================================================================
# Design Phase Schemas
# ============================================================================


class VariantSchema(BaseModel):
    """Schema for an experiment variant."""

    name: str = Field(..., description="Variant name (e.g., 'control', 'treatment')")
    description: str = Field(..., description="Variant description")
    traffic_percentage: float = Field(default=50.0, description="Traffic allocation %", ge=0, le=100)
    metadata: dict[str, Any] = Field(default_factory=dict, description="Variant metadata")


class DesignConfigSchema(BaseModel):
    """Schema for experiment design configuration."""

    hypothesis: HypothesisSchema = Field(..., description="Associated hypothesis")
    variants: list[VariantSchema] = Field(..., description="Experiment variants")
    primary_metric: str = Field(..., description="Primary metric name")
    metric_type: MetricType = Field(..., description="Type of primary metric")
    sample_size_per_variant: int = Field(..., description="Recommended sample size per variant")
    power: float = Field(default=0.8, description="Statistical power", ge=0.5, le=0.99)
    alpha: float = Field(default=0.05, description="Significance level", ge=0.01, le=0.1)
    randomization_unit: RandomizationUnit = Field(
        default=RandomizationUnit.USER, description="Unit of randomization"
    )
    estimated_duration_days: int = Field(..., description="Estimated runtime in days")
    guardrail_metrics: list[str] = Field(default_factory=list, description="Metrics to monitor")
    design_rationale: str = Field(..., description="Explanation of design choices")
    risks: list[str] = Field(default_factory=list, description="Potential risks")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# ============================================================================
# Analysis Phase Schemas
# ============================================================================


class StatisticalTestResultSchema(BaseModel):
    """Schema for statistical test results."""

    test_name: str = Field(..., description="Name of statistical test")
    metric: str = Field(..., description="Metric tested")
    control_mean: float = Field(..., description="Control variant mean")
    treatment_mean: float = Field(..., description="Treatment variant mean")
    p_value: float = Field(..., description="P-value from test")
    confidence_interval_lower: float = Field(..., description="CI lower bound")
    confidence_interval_upper: float = Field(..., description="CI upper bound")
    effect_size: float = Field(..., description="Effect size (relative difference)")
    is_significant: bool = Field(..., description="Whether result is statistically significant")
    sample_size_control: int = Field(..., description="Sample size for control")
    sample_size_treatment: int = Field(..., description="Sample size for treatment")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AnalysisResultSchema(BaseModel):
    """Schema for experiment analysis results."""

    test_results: list[StatisticalTestResultSchema] = Field(
        ..., description="Statistical test results"
    )
    primary_metric_significant: bool = Field(
        ..., description="Whether primary metric is significant"
    )
    guardrail_violations: list[str] = Field(
        default_factory=list, description="Guardrail metrics that regressed"
    )
    summary: str = Field(..., description="Plain English summary of results")
    key_findings: list[str] = Field(..., description="Key findings")
    confidence_assessment: str = Field(..., description="Assessment of result reliability")
    caveats: list[str] = Field(default_factory=list, description="Important caveats")
    data_quality_issues: list[str] = Field(default_factory=list, description="Data quality concerns")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# ============================================================================
# Decision Phase Schemas
# ============================================================================


class DecisionSchema(BaseModel):
    """Schema for final decision on experiment."""

    recommendation: DecisionRecommendation = Field(..., description="Recommendation: ship/no-ship/iterate")
    confidence: float = Field(..., description="Confidence in decision", ge=0, le=1)
    rationale: str = Field(..., description="Detailed reasoning")
    key_findings: list[str] = Field(..., description="Key findings driving decision")
    next_steps: list[str] = Field(..., description="Recommended actions")
    risks: list[str] = Field(default_factory=list, description="Risks to consider")
    business_impact: str = Field(..., description="Expected business impact")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# ============================================================================
# Experiment Lifecycle Schema
# ============================================================================


class ExperimentStateSchema(BaseModel):
    """Complete experiment through its lifecycle."""

    experiment_id: UUID = Field(..., description="Unique experiment ID")
    name: str = Field(..., description="Experiment name")
    status: str = Field(..., description="Current status")
    hypothesis: HypothesisSchema | None = Field(None, description="Generated hypothesis")
    design: DesignConfigSchema | None = Field(None, description="Experiment design")
    analysis: AnalysisResultSchema | None = Field(None, description="Analysis results")
    decision: DecisionSchema | None = Field(None, description="Final decision")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
