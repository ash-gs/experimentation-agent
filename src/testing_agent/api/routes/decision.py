"""Decision-making endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from ...agents.decision import DecisionAgent
from ..dependencies import get_decision_agent
from ..schemas import DecisionMakeRequest, DecisionMakeResponse

router = APIRouter()


@router.post("/make", response_model=DecisionMakeResponse)
async def make_decision(
    request: DecisionMakeRequest,
    agent: DecisionAgent = Depends(get_decision_agent),
) -> DecisionMakeResponse:
    """Make a ship/no-ship decision based on analysis results.

    Args:
        request: Decision request with analysis results
        agent: Injected decision agent

    Returns:
        Decision recommendation

    Raises:
        HTTPException: If decision making fails
    """
    try:
        decision = agent.make_decision(
            analysis=request.analysis,
            hypothesis=request.hypothesis,
            business_context=request.business_context,
        )

        return DecisionMakeResponse(
            success=True,
            message="Decision made successfully",
            decision=decision,
        )

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n{'='*80}\nDECISION ERROR:\n{'='*80}\n{error_details}{'='*80}\n")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to make decision: {type(e).__name__}: {str(e)}",
        )
