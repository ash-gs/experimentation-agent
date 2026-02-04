"""Decision-making agent for AB test experiments."""

from pathlib import Path
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field

from ..data.schemas import (
    AnalysisResultSchema,
    DecisionRecommendation,
    DecisionSchema,
    HypothesisSchema,
)
from ..utils.logging import get_logger
from .base import BaseAgent

logger = get_logger("agents.decision")


class DecisionOutput(BaseModel):
    """Structured output for decision making."""

    recommendation: str = Field(
        ..., description="Decision: ship, no_ship, iterate, or inconclusive"
    )
    confidence: float = Field(
        ..., description="Confidence in decision (0-1)", ge=0, le=1
    )
    rationale: str = Field(..., description="Detailed reasoning for the decision")
    key_findings: list[str] = Field(..., description="Key findings that drove the decision")
    next_steps: list[str] = Field(..., description="Recommended actions to take")
    risks: list[str] = Field(default_factory=list, description="Risks to consider")


class DecisionAgent(BaseAgent):
    """Agent specialized in making ship/no-ship decisions."""

    def __init__(self, **kwargs):
        """Initialize decision agent."""
        super().__init__(**kwargs)
        self.prompt_config = self._load_prompt_config()

    def _load_prompt_config(self) -> dict:
        """Load prompt configuration from YAML."""
        prompt_file = Path(__file__).parent.parent / "config" / "prompts" / "decision.yaml"

        if not prompt_file.exists():
            logger.warning(f"Prompt file not found: {prompt_file}, using default prompt")
            return {"system_prompt": self._get_default_system_prompt()}

        with open(prompt_file, "r") as f:
            return yaml.safe_load(f)

    def get_system_prompt(self) -> str:
        """Get the system prompt for decision making."""
        return self.prompt_config.get("system_prompt", self._get_default_system_prompt())

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt if YAML not found."""
        return """You are an expert AB testing decision agent. Your role is to make data-driven recommendations about whether to ship experiment changes.

Decision options:
- SHIP: Strong evidence of improvement, recommend rolling out
- NO_SHIP: Evidence of harm or no improvement, recommend not shipping
- ITERATE: Mixed results, recommend further testing or iteration
- INCONCLUSIVE: Insufficient data or unclear results

Always consider business impact, statistical rigor, and practical significance.
"""

    def make_decision(
        self,
        analysis: AnalysisResultSchema,
        hypothesis: HypothesisSchema | None = None,
        business_context: dict | None = None,
    ) -> DecisionSchema:
        """Make a ship/no-ship decision based on analysis results.

        Args:
            analysis: Analysis results from the experiment
            hypothesis: Original hypothesis (for context)
            business_context: Additional business context

        Returns:
            DecisionSchema with recommendation and rationale
        """
        logger.info(f"Making decision for experiment {analysis.experiment_id}")

        # Build context for LLM
        primary = analysis.primary_metric_result
        decision_context = {
            "p_value": f"{primary.p_value:.4f}",
            "statistically_significant": primary.statistically_significant,
            "practical_significance": primary.practical_significance,
            "control_rate": f"{primary.control_mean:.4f}",
            "treatment_rate": f"{primary.treatment_mean:.4f}",
            "effect_size": f"{primary.effect_size:.4f}",
            "relative_effect": f"{primary.relative_effect:.1f}%" if primary.relative_effect else "N/A",
            "confidence_interval": f"[{primary.confidence_interval_lower:.4f}, {primary.confidence_interval_upper:.4f}]",
            "sample_size_control": primary.control_n,
            "sample_size_treatment": primary.treatment_n,
            "sample_ratio_mismatch": analysis.sample_ratio_mismatch,
            "data_quality_issues": analysis.data_quality_issues or "None",
            "guardrail_violations": analysis.guardrail_violations or "None",
        }

        if hypothesis:
            decision_context["original_hypothesis"] = hypothesis.description
            decision_context["expected_effect"] = hypothesis.expected_effect_size
            decision_context["expected_direction"] = hypothesis.expected_direction.value

        if business_context:
            decision_context.update(business_context)

        # Get LLM decision
        prompt = self._build_decision_prompt(primary, analysis)

        output = self.invoke_structured(
            user_input=prompt,
            output_schema=DecisionOutput,
            context=decision_context,
        )

        # Map recommendation string to enum
        rec_map = {
            "ship": DecisionRecommendation.SHIP,
            "no_ship": DecisionRecommendation.NO_SHIP,
            "iterate": DecisionRecommendation.ITERATE,
            "inconclusive": DecisionRecommendation.INCONCLUSIVE,
        }
        recommendation = rec_map.get(
            output.recommendation.lower().replace(" ", "_"),
            DecisionRecommendation.INCONCLUSIVE,
        )

        # Build decision schema
        decision = DecisionSchema(
            decision_id=uuid4(),
            recommendation=recommendation,
            rationale=output.rationale,
            confidence=output.confidence,
            key_findings=output.key_findings,
            next_steps=output.next_steps,
            risks=output.risks if output.risks else None,
        )

        logger.info(
            f"Decision: {decision.recommendation.value} (confidence: {decision.confidence:.0%})"
        )

        return decision

    def _build_decision_prompt(
        self,
        primary: "StatisticalTestResultSchema",
        analysis: AnalysisResultSchema,
    ) -> str:
        """Build the decision prompt."""
        significance_status = "SIGNIFICANT" if primary.statistically_significant else "NOT SIGNIFICANT"
        direction = "positive" if primary.effect_size > 0 else "negative"

        prompt = f"""Based on these AB test results, make a ship/no-ship recommendation:

## Results Summary
- Control: {primary.control_mean:.2%} ({primary.control_n:,} users)
- Treatment: {primary.treatment_mean:.2%} ({primary.treatment_n:,} users)
- Effect: {primary.effect_size:+.2%} ({direction})
- Relative lift: {primary.relative_effect:+.1f}%
- P-value: {primary.p_value:.4f} ({significance_status})
- 95% CI: [{primary.confidence_interval_lower:.4f}, {primary.confidence_interval_upper:.4f}]

## Data Quality
- Sample Ratio Mismatch: {"YES - INVESTIGATE" if analysis.sample_ratio_mismatch else "No"}
- Data Issues: {analysis.data_quality_issues or "None detected"}
- Guardrail Violations: {analysis.guardrail_violations or "None"}

What is your recommendation? Consider statistical significance, practical significance, and data quality."""

        return prompt

    def make_decision_interactive(
        self,
        results_summary: str,
        context: dict | None = None,
    ) -> str:
        """Make decision with conversational response.

        Args:
            results_summary: Natural language summary of results
            context: Optional additional context

        Returns:
            Natural language decision with rationale
        """
        logger.info("Making interactive decision")

        prompt = f"Based on these experiment results, should we ship? {results_summary}"
        return self.invoke(prompt, context=context)
