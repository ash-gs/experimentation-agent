"""Hypothesis generation agent."""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from ..data.schemas import Direction, HypothesisSchema
from ..utils.logging import get_logger
from .base import BaseAgent

logger = get_logger("agents.hypothesis")


class HypothesisOutput(BaseModel):
    """Structured output for hypothesis generation."""

    hypothesis_description: str = Field(
        ..., description="Clear, testable hypothesis statement"
    )
    primary_metric: str = Field(..., description="Primary metric to measure")
    expected_direction: Direction = Field(..., description="Expected direction of change")
    expected_effect_size: float = Field(
        ..., description="Expected effect size (absolute)", gt=0
    )
    rationale: str = Field(..., description="Why this hypothesis makes sense")
    is_testable: bool = Field(True, description="Whether hypothesis is testable")
    is_specific: bool = Field(True, description="Whether hypothesis is specific")
    is_measurable: bool = Field(True, description="Whether hypothesis is measurable")


class HypothesisAgent(BaseAgent):
    """Agent specialized in generating AB test hypotheses."""

    def __init__(self, **kwargs):
        """Initialize hypothesis agent."""
        super().__init__(**kwargs)
        self.prompt_config = self._load_prompt_config()

    def _load_prompt_config(self) -> dict:
        """Load prompt configuration from YAML."""
        prompt_file = Path(__file__).parent.parent / "config" / "prompts" / "hypothesis.yaml"

        if not prompt_file.exists():
            logger.warning(f"Prompt file not found: {prompt_file}, using default prompt")
            return {"system_prompt": self._get_default_system_prompt()}

        with open(prompt_file, "r") as f:
            return yaml.safe_load(f)

    def get_system_prompt(self) -> str:
        """Get the system prompt for hypothesis generation."""
        return self.prompt_config.get("system_prompt", self._get_default_system_prompt())

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt if YAML not found."""
        return """You are an expert AB testing hypothesis agent. Your role is to help users formulate testable, measurable hypotheses for experiments.

A good hypothesis must be:
- Testable: Can be validated through an A/B test
- Specific: Clearly states what will change
- Measurable: Defines a clear metric
- Directional: States whether metric should increase or decrease
- Realistic: Effect size should be achievable

Format: "Changing [WHAT] will [DIRECTION] [METRIC] by [EFFECT SIZE]."
"""

    def generate_hypothesis(
        self, business_goal: str, context: dict | None = None
    ) -> HypothesisSchema:
        """Generate a testable hypothesis from a business goal.

        Args:
            business_goal: User's business goal or problem statement
            context: Optional additional context (current metrics, constraints, etc.)

        Returns:
            HypothesisSchema with generated hypothesis
        """
        logger.info(f"Generating hypothesis for goal: {business_goal[:50]}...")

        # Invoke agent with structured output
        output = self.invoke_structured(
            user_input=business_goal,
            output_schema=HypothesisOutput,
            context=context,
        )

        # Convert to HypothesisSchema
        hypothesis = HypothesisSchema(
            description=output.hypothesis_description,
            metric=output.primary_metric,
            expected_direction=output.expected_direction,
            expected_effect_size=output.expected_effect_size,
            rationale=output.rationale,
        )

        logger.info(f"Generated hypothesis: {hypothesis.description[:80]}...")

        return hypothesis

    def generate_hypothesis_interactive(self, business_goal: str) -> str:
        """Generate hypothesis with conversational response (non-structured).

        Args:
            business_goal: User's business goal

        Returns:
            Natural language response with hypothesis
        """
        logger.info(f"Generating interactive hypothesis for: {business_goal[:50]}...")

        response = self.invoke(user_input=business_goal)

        return response
