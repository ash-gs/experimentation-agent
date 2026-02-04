"""Hypothesis generation endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from ...agents.hypothesis import HypothesisAgent
from ..dependencies import get_hypothesis_agent
from ..schemas import HypothesisGenerateRequest, HypothesisGenerateResponse

router = APIRouter()


@router.post("/generate", response_model=HypothesisGenerateResponse)
async def generate_hypothesis(
    request: HypothesisGenerateRequest,
    agent: HypothesisAgent = Depends(get_hypothesis_agent),
) -> HypothesisGenerateResponse:
    """Generate a testable hypothesis from a business goal.

    Args:
        request: Hypothesis generation request
        agent: Injected hypothesis agent

    Returns:
        Generated hypothesis

    Raises:
        HTTPException: If hypothesis generation fails
    """
    try:
        hypothesis = agent.generate_hypothesis(
            business_goal=request.business_goal,
            context=request.context,
        )

        return HypothesisGenerateResponse(
            success=True,
            message="Hypothesis generated successfully",
            hypothesis=hypothesis,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate hypothesis: {str(e)}",
        )
