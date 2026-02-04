"""Predefined synthetic experiment scenarios."""

from dataclasses import dataclass
from enum import Enum

from ..data.schemas import Direction, MetricType


class ScenarioType(str, Enum):
    """Types of predefined scenarios."""

    BUTTON_COLOR_POSITIVE = "button_color_positive"
    HEADLINE_NULL = "headline_null"
    FORM_NEGATIVE = "form_negative"
    REVENUE_POSITIVE = "revenue_positive"
    UNBALANCED_SRM = "unbalanced_srm"


@dataclass
class ScenarioConfig:
    """Configuration for a synthetic experiment scenario."""

    name: str
    description: str
    hypothesis: str
    metric_name: str
    metric_type: MetricType
    expected_direction: Direction

    # Control variant
    control_name: str
    control_description: str
    control_rate: float  # Baseline conversion rate or mean

    # Treatment variant
    treatment_name: str
    treatment_description: str
    treatment_rate: float  # Treatment conversion rate or mean

    # Experiment parameters
    sample_size_per_variant: int
    duration_days: int
    noise_std: float = 0.0  # Standard deviation for noise

    # Optional
    has_srm: bool = False  # Sample ratio mismatch
    data_quality_issues: list[str] | None = None


# Predefined scenarios

BUTTON_COLOR_POSITIVE = ScenarioConfig(
    name="Button Color A/B Test (Positive Effect)",
    description="Test changing checkout button from green to red",
    hypothesis="Changing the checkout button color from green to red will increase conversion rate by 0.5 percentage points",
    metric_name="conversion_rate",
    metric_type=MetricType.BINARY,
    expected_direction=Direction.INCREASE,
    control_name="control_green",
    control_description="Green checkout button (current)",
    control_rate=0.05,  # 5% baseline conversion
    treatment_name="treatment_red",
    treatment_description="Red checkout button (new)",
    treatment_rate=0.055,  # 5.5% conversion (0.5pp lift)
    sample_size_per_variant=50000,
    duration_days=14,
    noise_std=0.0,
)

HEADLINE_NULL = ScenarioConfig(
    name="Homepage Headline Test (Null Result)",
    description="Test new homepage headline with no real effect",
    hypothesis="Changing the homepage headline will increase signup rate",
    metric_name="signup_rate",
    metric_type=MetricType.BINARY,
    expected_direction=Direction.INCREASE,
    control_name="control_original",
    control_description="Original headline",
    control_rate=0.03,  # 3% baseline signup rate
    treatment_name="treatment_new",
    treatment_description="New headline",
    treatment_rate=0.0305,  # 3.05% (tiny, insignificant difference)
    sample_size_per_variant=50000,
    duration_days=14,
    noise_std=0.0,
)

FORM_NEGATIVE = ScenarioConfig(
    name="Form Simplification (Negative Effect)",
    description="Simplifying form accidentally reduces completions",
    hypothesis="Reducing form fields from 5 to 3 will increase completion rate",
    metric_name="form_completion_rate",
    metric_type=MetricType.BINARY,
    expected_direction=Direction.INCREASE,
    control_name="control_5fields",
    control_description="5-field form (current)",
    control_rate=0.60,  # 60% completion rate
    treatment_name="treatment_3fields",
    treatment_description="3-field simplified form",
    treatment_rate=0.55,  # 55% completion (negative impact!)
    sample_size_per_variant=30000,
    duration_days=10,
    noise_std=0.0,
)

REVENUE_POSITIVE = ScenarioConfig(
    name="Pricing Test (Revenue Impact)",
    description="Test higher price point with premium features",
    hypothesis="Increasing price from $9.99 to $12.99 with more features will increase revenue per user",
    metric_name="revenue_per_user",
    metric_type=MetricType.CONTINUOUS,
    expected_direction=Direction.INCREASE,
    control_name="control_999",
    control_description="$9.99/month pricing",
    control_rate=2.5,  # $2.50 average revenue per user
    treatment_name="treatment_1299",
    treatment_description="$12.99/month with premium features",
    treatment_rate=3.2,  # $3.20 average (28% increase)
    sample_size_per_variant=100000,
    duration_days=21,
    noise_std=5.0,  # Revenue has higher variance
)

UNBALANCED_SRM = ScenarioConfig(
    name="Sample Ratio Mismatch Detection",
    description="Test with unbalanced assignment (50/50 becomes 45/55)",
    hypothesis="Testing SRM detection capabilities",
    metric_name="conversion_rate",
    metric_type=MetricType.BINARY,
    expected_direction=Direction.INCREASE,
    control_name="control",
    control_description="Control variant",
    control_rate=0.05,
    treatment_name="treatment",
    treatment_description="Treatment variant",
    treatment_rate=0.055,
    sample_size_per_variant=50000,  # But will be unbalanced
    duration_days=14,
    has_srm=True,  # Intentionally unbalanced
)

# Scenario registry
SCENARIOS = {
    ScenarioType.BUTTON_COLOR_POSITIVE: BUTTON_COLOR_POSITIVE,
    ScenarioType.HEADLINE_NULL: HEADLINE_NULL,
    ScenarioType.FORM_NEGATIVE: FORM_NEGATIVE,
    ScenarioType.REVENUE_POSITIVE: REVENUE_POSITIVE,
    ScenarioType.UNBALANCED_SRM: UNBALANCED_SRM,
}


def get_scenario(scenario_type: ScenarioType) -> ScenarioConfig:
    """Get a predefined scenario by type."""
    return SCENARIOS[scenario_type]
