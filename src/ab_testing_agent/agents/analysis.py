"""Statistical analysis agent."""

from pathlib import Path
from uuid import UUID, uuid4

import pandas as pd
import yaml
from pydantic import BaseModel, Field

from ..data.schemas import (
    AnalysisResultSchema,
    DesignConfigSchema,
    MetricType,
    StatisticalTestResultSchema,
)
from ..tools.statistical.hypothesis_testing import (
    two_proportion_ztest,
    two_sample_ttest,
)
from ..tools.statistical.metrics import (
    aggregate_continuous_metric,
    aggregate_conversion_rate,
    detect_sample_ratio_mismatch,
    validate_experiment_data,
)
from ..utils.logging import get_logger
from .base import BaseAgent

logger = get_logger("agents.analysis")


class AnalysisInterpretation(BaseModel):
    """LLM interpretation of statistical results."""

    summary: str = Field(..., description="Plain English summary of results")
    key_findings: list[str] = Field(..., description="Bullet points of key findings")
    confidence_assessment: str = Field(..., description="Assessment of result reliability")
    caveats: list[str] = Field(default_factory=list, description="Important caveats or limitations")
    recommendation_preview: str = Field(..., description="Initial recommendation based on data")


class AnalysisAgent(BaseAgent):
    """Agent specialized in analyzing AB test results."""

    def __init__(self, **kwargs):
        """Initialize analysis agent."""
        super().__init__(**kwargs)
        self.prompt_config = self._load_prompt_config()

    def _load_prompt_config(self) -> dict:
        """Load prompt configuration from YAML."""
        prompt_file = Path(__file__).parent.parent / "config" / "prompts" / "analysis.yaml"

        if not prompt_file.exists():
            logger.warning(f"Prompt file not found: {prompt_file}, using default prompt")
            return {"system_prompt": self._get_default_system_prompt()}

        with open(prompt_file, "r") as f:
            return yaml.safe_load(f)

    def get_system_prompt(self) -> str:
        """Get the system prompt for analysis."""
        return self.prompt_config.get("system_prompt", self._get_default_system_prompt())

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt if YAML not found."""
        return """You are an expert AB testing analysis agent. Your role is to interpret statistical results and explain them clearly.

You help with:
- Interpreting p-values and confidence intervals
- Explaining effect sizes in business terms
- Identifying data quality issues
- Providing balanced, honest assessments

Always be honest about uncertainty and limitations.
"""

    def analyze_experiment(
        self,
        events: pd.DataFrame,
        experiment_id: UUID,
        design: DesignConfigSchema | None = None,
        metric_type: MetricType = MetricType.BINARY,
        alpha: float = 0.05,
        control_name: str = "control",
        treatment_name: str = "treatment",
    ) -> AnalysisResultSchema:
        """Analyze experiment data and return statistical results.

        Args:
            events: DataFrame with experiment events
            experiment_id: ID of the experiment
            design: Optional design config for context
            metric_type: Type of metric (binary or continuous)
            alpha: Significance level
            control_name: Name of control variant
            treatment_name: Name of treatment variant

        Returns:
            AnalysisResultSchema with complete analysis
        """
        logger.info(f"Analyzing experiment {experiment_id}")

        # Validate data
        is_valid, issues = validate_experiment_data(
            events,
            control_name=control_name,
            treatment_name=treatment_name,
        )

        data_quality_issues = issues if issues else None

        # Check for SRM
        control_metric = aggregate_conversion_rate(events, control_name)
        treatment_metric = aggregate_conversion_rate(events, treatment_name)

        srm_result = detect_sample_ratio_mismatch(
            control_n=control_metric.total,
            treatment_n=treatment_metric.total,
        )

        # Run appropriate statistical test
        if metric_type == MetricType.BINARY:
            primary_result = self._analyze_binary_metric(
                events, control_name, treatment_name, alpha
            )
        else:
            primary_result = self._analyze_continuous_metric(
                events, control_name, treatment_name, alpha
            )

        # Get LLM interpretation
        interpretation = self._get_interpretation(
            primary_result, srm_result.is_srm_detected, data_quality_issues
        )

        # Build analysis result
        analysis = AnalysisResultSchema(
            analysis_id=uuid4(),
            experiment_id=experiment_id,
            primary_metric_result=primary_result,
            secondary_metrics=None,
            guardrail_violations=None,
            sample_ratio_mismatch=srm_result.is_srm_detected,
            data_quality_issues=data_quality_issues,
            interpretation=interpretation,
        )

        logger.info(
            f"Analysis complete: p={primary_result.p_value:.4f}, "
            f"significant={primary_result.statistically_significant}"
        )

        return analysis

    def _analyze_binary_metric(
        self,
        events: pd.DataFrame,
        control_name: str,
        treatment_name: str,
        alpha: float,
    ) -> StatisticalTestResultSchema:
        """Analyze binary (conversion) metric."""
        control = aggregate_conversion_rate(events, control_name)
        treatment = aggregate_conversion_rate(events, treatment_name)

        result = two_proportion_ztest(
            control_successes=control.successes,
            control_n=control.total,
            treatment_successes=treatment.successes,
            treatment_n=treatment.total,
            alpha=alpha,
        )

        return result

    def _analyze_continuous_metric(
        self,
        events: pd.DataFrame,
        control_name: str,
        treatment_name: str,
        alpha: float,
        metric_col: str = "metric_value",
    ) -> StatisticalTestResultSchema:
        """Analyze continuous metric."""
        control = aggregate_continuous_metric(events, control_name, metric_col=metric_col)
        treatment = aggregate_continuous_metric(events, treatment_name, metric_col=metric_col)

        if len(control.values) < 2 or len(treatment.values) < 2:
            raise ValueError("Insufficient data for continuous metric analysis")

        result = two_sample_ttest(
            control_data=control.values,
            treatment_data=treatment.values,
            alpha=alpha,
        )

        return result

    def _get_interpretation(
        self,
        result: StatisticalTestResultSchema,
        srm_detected: bool,
        data_issues: list[str] | None,
    ) -> str:
        """Get LLM interpretation of results."""
        # Build context for LLM
        context = {
            "p_value": f"{result.p_value:.4f}",
            "statistically_significant": result.statistically_significant,
            "control_rate": f"{result.control_mean:.4f}",
            "treatment_rate": f"{result.treatment_mean:.4f}",
            "effect_size": f"{result.effect_size:.4f}",
            "relative_effect": f"{result.relative_effect:.1f}%" if result.relative_effect else "N/A",
            "confidence_interval": f"[{result.confidence_interval_lower:.4f}, {result.confidence_interval_upper:.4f}]",
            "sample_ratio_mismatch": srm_detected,
            "data_quality_issues": data_issues or "None",
        }

        prompt = f"""Interpret these AB test results:

Control: {result.control_mean:.2%} ({result.control_n:,} users)
Treatment: {result.treatment_mean:.2%} ({result.treatment_n:,} users)
Absolute difference: {result.effect_size:.2%}
Relative lift: {result.relative_effect:.1f}% if result.relative_effect else 'N/A'
P-value: {result.p_value:.4f}
95% CI: [{result.confidence_interval_lower:.4f}, {result.confidence_interval_upper:.4f}]
Statistically significant: {result.statistically_significant}
SRM detected: {srm_detected}
Data issues: {data_issues or 'None'}

Provide a clear, honest interpretation in 2-3 sentences."""

        try:
            interpretation = self.invoke(prompt, context=context)
            return interpretation
        except Exception as e:
            logger.warning(f"Failed to get LLM interpretation: {e}")
            # Fallback to simple interpretation
            if result.statistically_significant:
                return f"The experiment shows a statistically significant effect (p={result.p_value:.4f}). Treatment {'outperformed' if result.effect_size > 0 else 'underperformed'} control by {abs(result.relative_effect or 0):.1f}%."
            else:
                return f"The experiment did not reach statistical significance (p={result.p_value:.4f}). The observed difference may be due to chance."

    def analyze_experiment_interactive(
        self,
        summary_stats: dict,
    ) -> str:
        """Provide interactive analysis of experiment results.

        Args:
            summary_stats: Dictionary with summary statistics

        Returns:
            Natural language analysis
        """
        prompt = f"Analyze these AB test results and explain the findings: {summary_stats}"
        return self.invoke(prompt, context=summary_stats)
