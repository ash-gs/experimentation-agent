"""Analysis endpoints."""

from uuid import uuid4

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from ...agents.analysis import AnalysisAgent
from ...data.schemas import MetricType
from ..dependencies import get_analysis_agent
from ..schemas import AnalysisAnalyzeRequest, AnalysisAnalyzeResponse

router = APIRouter()


@router.post("/analyze", response_model=AnalysisAnalyzeResponse)
async def analyze_experiment(
    request: AnalysisAnalyzeRequest,
    agent: AnalysisAgent = Depends(get_analysis_agent),
) -> AnalysisAnalyzeResponse:
    """Analyze experiment results.

    Args:
        request: Analysis request with control and treatment data
        agent: Injected analysis agent

    Returns:
        Analysis results

    Raises:
        HTTPException: If analysis fails
    """
    try:
        # Convert dict data to DataFrame format
        # Expecting data like: {"metric_value": [...], "user_id": [...], "variant": [...]}
        events_data = []

        # Add control data
        if isinstance(request.control_data.get("values"), list):
            for i, value in enumerate(request.control_data["values"]):
                events_data.append({
                    "user_id": f"control_user_{i}",
                    "variant_name": "control",
                    "event_type": "conversion" if value > 0 else "exposure",
                    "metric_value": value,
                    "converted": value if isinstance(value, bool) else value > 0,
                })

        # Add treatment data
        if isinstance(request.treatment_data.get("values"), list):
            for i, value in enumerate(request.treatment_data["values"]):
                events_data.append({
                    "user_id": f"treatment_user_{i}",
                    "variant_name": "treatment",
                    "event_type": "conversion" if value > 0 else "exposure",
                    "metric_value": value,
                    "converted": value if isinstance(value, bool) else value > 0,
                })

        events_df = pd.DataFrame(events_data)

        # Determine metric type
        metric_type = request.design.metric_type if hasattr(request.design, "metric_type") else MetricType.BINARY

        analysis = agent.analyze_experiment(
            events=events_df,
            experiment_id=uuid4(),  # Generate temp ID
            design=request.design,
            metric_type=metric_type,
        )

        return AnalysisAnalyzeResponse(
            success=True,
            message="Analysis completed successfully",
            analysis=analysis,
        )

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n{'='*80}\nANALYSIS ERROR:\n{'='*80}\n{error_details}{'='*80}\n")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze experiment: {type(e).__name__}: {str(e)}",
        )
