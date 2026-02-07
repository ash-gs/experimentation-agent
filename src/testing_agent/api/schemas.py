"""Request and response schemas for API endpoints."""

from typing import Any

from pydantic import BaseModel, Field

from ..data.schemas import (
    AnalysisResultSchema,
    DecisionSchema,
    DesignConfigSchema,
    HypothesisSchema,
)


# ============================================================================
# Base Response
# ============================================================================


class APIResponse(BaseModel):
    """Base API response."""

    success: bool = Field(default=True, description="Whether request succeeded")
    message: str = Field(default="Success", description="Response message")


# ============================================================================
# Hypothesis Endpoints
# ============================================================================


class HypothesisGenerateRequest(BaseModel):
    """Request to generate a hypothesis."""

    business_goal: str = Field(..., description="Business goal or problem statement")
    context: dict[str, Any] | None = Field(None, description="Additional context")


class HypothesisGenerateResponse(APIResponse):
    """Response from hypothesis generation."""

    hypothesis: HypothesisSchema | None = None


# ============================================================================
# Design Endpoints
# ============================================================================


class DesignCreateRequest(BaseModel):
    """Request to design an experiment."""

    hypothesis: HypothesisSchema = Field(..., description="Hypothesis to design for")
    traffic_percentage: float = Field(default=100.0, description="% of traffic to include", ge=1, le=100)
    daily_users: int | None = Field(None, description="Estimated daily users")
    context: dict[str, Any] | None = Field(None, description="Additional context")


class DesignCreateResponse(APIResponse):
    """Response from experiment design."""

    design: DesignConfigSchema | None = None


# ============================================================================
# Analysis Endpoints
# ============================================================================


class AnalysisAnalyzeRequest(BaseModel):
    """Request to analyze experiment results."""

    control_data: dict[str, Any] = Field(..., description="Control variant data")
    treatment_data: dict[str, Any] = Field(..., description="Treatment variant data")
    design: DesignConfigSchema = Field(..., description="Experiment design config")
    hypothesis: HypothesisSchema | None = Field(None, description="Original hypothesis")


class AnalysisAnalyzeResponse(APIResponse):
    """Response from analysis."""

    analysis: AnalysisResultSchema | None = None


# ============================================================================
# Decision Endpoints
# ============================================================================


class DecisionMakeRequest(BaseModel):
    """Request to make a decision."""

    analysis: AnalysisResultSchema = Field(..., description="Analysis results")
    hypothesis: HypothesisSchema | None = Field(None, description="Original hypothesis")
    business_context: dict[str, Any] | None = Field(None, description="Business context")


class DecisionMakeResponse(APIResponse):
    """Response from decision making."""

    decision: DecisionSchema | None = None
