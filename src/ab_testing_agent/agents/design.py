"""Experiment design agent."""

from pathlib import Path
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field

from ..data.schemas import (
    DesignConfigSchema,
    HypothesisSchema,
    RandomizationUnit,
    VariantSchema,
)
from ..tools.statistical.power_analysis import (
    calculate_sample_size,
    estimate_duration,
)
from ..utils.logging import get_logger
from .base import BaseAgent

logger = get_logger("agents.design")


class DesignOutput(BaseModel):
    """Structured output for experiment design."""

    control_name: str = Field(default="control", description="Name of control variant")
    control_description: str = Field(..., description="Description of control variant")
    treatment_name: str = Field(default="treatment", description="Name of treatment variant")
    treatment_description: str = Field(..., description="Description of treatment variant")
    traffic_allocation_percent: float = Field(
        default=50.0, description="Traffic % per variant", ge=10, le=90
    )
    recommended_power: float = Field(default=0.8, description="Recommended statistical power")
    recommended_alpha: float = Field(default=0.05, description="Recommended significance level")
    randomization_unit: str = Field(default="user", description="Unit of randomization")
    guardrail_metrics: list[str] = Field(
        default_factory=list, description="Metrics to monitor for regressions"
    )
    risks: list[str] = Field(default_factory=list, description="Potential risks or concerns")
    design_rationale: str = Field(..., description="Explanation of design choices")


class DesignAgent(BaseAgent):
    """Agent specialized in designing AB test experiments."""

    def __init__(self, **kwargs):
        """Initialize design agent."""
        super().__init__(**kwargs)
        self.prompt_config = self._load_prompt_config()

    def _load_prompt_config(self) -> dict:
        """Load prompt configuration from YAML."""
        prompt_file = Path(__file__).parent.parent / "config" / "prompts" / "design.yaml"

        if not prompt_file.exists():
            logger.warning(f"Prompt file not found: {prompt_file}, using default prompt")
            return {"system_prompt": self._get_default_system_prompt()}

        with open(prompt_file, "r") as f:
            return yaml.safe_load(f)

    def get_system_prompt(self) -> str:
        """Get the system prompt for experiment design."""
        return self.prompt_config.get("system_prompt", self._get_default_system_prompt())

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt if YAML not found."""
        return """You are an expert AB testing experiment design agent. Your role is to design statistically rigorous experiments.

You help with:
- Defining control and treatment variants
- Recommending traffic allocation
- Identifying guardrail metrics
- Assessing risks and concerns

Always design for statistical rigor while considering practical constraints.
"""

    def design_experiment(
        self,
        hypothesis: HypothesisSchema,
        daily_traffic: int | None = None,
        baseline_rate: float | None = None,
        context: dict | None = None,
    ) -> DesignConfigSchema:
        """Design an experiment based on a hypothesis.

        Args:
            hypothesis: The hypothesis to test
            daily_traffic: Expected daily unique users (for duration estimate)
            baseline_rate: Current baseline metric rate (for sample size calculation)
            context: Optional additional context

        Returns:
            DesignConfigSchema with complete experiment design
        """
        logger.info(f"Designing experiment for hypothesis: {hypothesis.description[:50]}...")

        # Build context for LLM
        design_context = context or {}
        design_context["hypothesis"] = hypothesis.description
        design_context["metric"] = hypothesis.metric
        design_context["expected_direction"] = hypothesis.expected_direction.value
        design_context["expected_effect_size"] = hypothesis.expected_effect_size

        if daily_traffic:
            design_context["daily_traffic"] = daily_traffic
        if baseline_rate:
            design_context["baseline_rate"] = baseline_rate

        # Get LLM recommendations for qualitative aspects
        output = self.invoke_structured(
            user_input=f"Design an experiment to test this hypothesis: {hypothesis.description}",
            output_schema=DesignOutput,
            context=design_context,
        )

        # Calculate sample size using statistical tools
        mde = hypothesis.expected_effect_size
        base_rate = baseline_rate or 0.05  # Default assumption

        try:
            sample_size = calculate_sample_size(
                baseline_rate=base_rate,
                mde=mde,
                power=output.recommended_power,
                alpha=output.recommended_alpha,
            )
        except Exception as e:
            logger.warning(f"Sample size calculation failed: {e}, using default")
            sample_size = 10000  # Fallback default

        # Estimate duration if traffic provided
        if daily_traffic:
            duration_days = estimate_duration(
                sample_size_per_variant=sample_size,
                daily_traffic=daily_traffic,
                num_variants=2,
            )
        else:
            duration_days = 14  # Default 2 weeks

        # Build variants
        control_variant = VariantSchema(
            variant_id=uuid4(),
            name=output.control_name,
            description=output.control_description,
            allocation_percent=output.traffic_allocation_percent,
            is_control=True,
        )

        treatment_variant = VariantSchema(
            variant_id=uuid4(),
            name=output.treatment_name,
            description=output.treatment_description,
            allocation_percent=output.traffic_allocation_percent,
            is_control=False,
        )

        # Map randomization unit
        rand_unit_map = {
            "user": RandomizationUnit.USER,
            "session": RandomizationUnit.SESSION,
            "request": RandomizationUnit.REQUEST,
        }
        randomization_unit = rand_unit_map.get(
            output.randomization_unit.lower(), RandomizationUnit.USER
        )

        # Build design config
        design = DesignConfigSchema(
            variants=[control_variant, treatment_variant],
            sample_size_per_variant=sample_size,
            duration_days=duration_days,
            power=output.recommended_power,
            significance_level=output.recommended_alpha,
            minimum_detectable_effect=mde,
            randomization_unit=randomization_unit,
            traffic_allocation=output.traffic_allocation_percent / 100 * 2,  # Total traffic
        )

        logger.info(
            f"Designed experiment: {sample_size:,} users/variant, {duration_days} days"
        )

        return design

    def design_experiment_interactive(
        self, hypothesis_description: str, context: dict | None = None
    ) -> str:
        """Design experiment with conversational response.

        Args:
            hypothesis_description: Natural language hypothesis
            context: Optional context

        Returns:
            Natural language response with design recommendations
        """
        logger.info(f"Interactive design for: {hypothesis_description[:50]}...")

        response = self.invoke(
            user_input=f"Help me design an experiment to test: {hypothesis_description}",
            context=context,
        )

        return response
