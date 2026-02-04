"""Experiment design endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from ...agents.design import DesignAgent
from ..dependencies import get_design_agent
from ..schemas import DesignCreateRequest, DesignCreateResponse

router = APIRouter()


@router.post("/create", response_model=DesignCreateResponse)
async def create_design(
    request: DesignCreateRequest,
    agent: DesignAgent = Depends(get_design_agent),
) -> DesignCreateResponse:
    """Design an experiment based on a hypothesis.

    Args:
        request: Design creation request
        agent: Injected design agent

    Returns:
        Experiment design configuration

    Raises:
        HTTPException: If design creation fails
    """
    try:
        design = agent.design_experiment(
            hypothesis=request.hypothesis,
            daily_traffic=request.daily_users,
            context=request.context,
        )

        return DesignCreateResponse(
            success=True,
            message="Experiment design created successfully",
            design=design,
        )

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n{'='*80}\nFULL ERROR TRACEBACK:\n{'='*80}\n{error_details}{'='*80}\n")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create experiment design: {type(e).__name__}: {str(e)}",
        )
