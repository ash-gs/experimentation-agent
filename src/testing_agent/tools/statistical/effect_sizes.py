"""Effect size calculations for AB testing."""

import math
from typing import NamedTuple

import numpy as np


class EffectSizeResult(NamedTuple):
    """Effect size calculation result."""
    value: float
    interpretation: str
    metric_name: str


def _interpret_cohens_d(d: float) -> str:
    """Interpret Cohen's d effect size."""
    if d < 0.2:
        return "negligible"
    elif d < 0.5:
        return "small"
    elif d < 0.8:
        return "medium"
    else:
        return "large"


def cohens_d(
    control_data: list[float] | np.ndarray,
    treatment_data: list[float] | np.ndarray,
    pooled: bool = True,
) -> EffectSizeResult:
    """Calculate Cohen's d effect size for continuous metrics."""
    control = np.asarray(control_data)
    treatment = np.asarray(treatment_data)

    n1, n2 = len(control), len(treatment)
    if n1 < 2 or n2 < 2:
        raise ValueError("Need at least 2 data points per group")

    mean1, mean2 = np.mean(control), np.mean(treatment)
    var1, var2 = np.var(control, ddof=1), np.var(treatment, ddof=1)

    if pooled:
        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
        pooled_std = math.sqrt(pooled_var)
        d = (mean2 - mean1) / pooled_std if pooled_std > 0 else 0.0
    else:
        std1 = math.sqrt(var1)
        d = (mean2 - mean1) / std1 if std1 > 0 else 0.0

    return EffectSizeResult(
        value=float(d),
        interpretation=_interpret_cohens_d(abs(d)),
        metric_name="Cohen's d",
    )


def cohens_h(control_rate: float, treatment_rate: float) -> EffectSizeResult:
    """Calculate Cohen's h effect size for proportions."""
    if not 0 <= control_rate <= 1:
        raise ValueError("control_rate must be between 0 and 1")
    if not 0 <= treatment_rate <= 1:
        raise ValueError("treatment_rate must be between 0 and 1")

    phi1 = 2 * math.asin(math.sqrt(control_rate))
    phi2 = 2 * math.asin(math.sqrt(treatment_rate))
    h = phi2 - phi1

    return EffectSizeResult(
        value=float(h),
        interpretation=_interpret_cohens_d(abs(h)),
        metric_name="Cohen's h",
    )


def relative_lift(control_value: float, treatment_value: float) -> EffectSizeResult:
    """Calculate relative lift (percentage change)."""
    if control_value == 0:
        raise ValueError("control_value cannot be zero")

    lift_pct = (treatment_value - control_value) / control_value * 100
    abs_lift = abs(lift_pct)

    if abs_lift < 1:
        interpretation = "negligible"
    elif abs_lift < 5:
        interpretation = "small"
    elif abs_lift < 10:
        interpretation = "medium"
    else:
        interpretation = "large"

    return EffectSizeResult(
        value=float(lift_pct),
        interpretation=interpretation,
        metric_name="relative_lift_percent",
    )


def absolute_difference(control_value: float, treatment_value: float) -> EffectSizeResult:
    """Calculate absolute difference."""
    diff = treatment_value - control_value
    return EffectSizeResult(
        value=float(diff),
        interpretation="n/a",
        metric_name="absolute_difference",
    )


def odds_ratio(control_rate: float, treatment_rate: float) -> EffectSizeResult:
    """Calculate odds ratio between two proportions."""
    if not 0 < control_rate < 1:
        raise ValueError("control_rate must be between 0 and 1 (exclusive)")
    if not 0 < treatment_rate < 1:
        raise ValueError("treatment_rate must be between 0 and 1 (exclusive)")

    control_odds = control_rate / (1 - control_rate)
    treatment_odds = treatment_rate / (1 - treatment_rate)
    or_value = treatment_odds / control_odds

    if 0.9 <= or_value <= 1.1:
        interpretation = "negligible"
    elif 0.67 <= or_value <= 1.5:
        interpretation = "small"
    elif 0.4 <= or_value <= 2.5:
        interpretation = "medium"
    else:
        interpretation = "large"

    return EffectSizeResult(
        value=float(or_value),
        interpretation=interpretation,
        metric_name="odds_ratio",
    )


def risk_ratio(control_rate: float, treatment_rate: float) -> EffectSizeResult:
    """Calculate risk ratio (relative risk)."""
    if control_rate <= 0:
        raise ValueError("control_rate must be positive")
    if treatment_rate < 0:
        raise ValueError("treatment_rate cannot be negative")

    rr = treatment_rate / control_rate

    if 0.95 <= rr <= 1.05:
        interpretation = "negligible"
    elif 0.8 <= rr <= 1.25:
        interpretation = "small"
    elif 0.5 <= rr <= 2.0:
        interpretation = "medium"
    else:
        interpretation = "large"

    return EffectSizeResult(
        value=float(rr),
        interpretation=interpretation,
        metric_name="risk_ratio",
    )


def number_needed_to_treat(control_rate: float, treatment_rate: float) -> EffectSizeResult:
    """Calculate Number Needed to Treat (NNT)."""
    diff = abs(treatment_rate - control_rate)
    if diff == 0:
        return EffectSizeResult(
            value=float("inf"),
            interpretation="no effect",
            metric_name="NNT",
        )

    nnt = 1 / diff

    if nnt <= 10:
        interpretation = "very strong effect"
    elif nnt <= 50:
        interpretation = "strong effect"
    elif nnt <= 100:
        interpretation = "moderate effect"
    else:
        interpretation = "weak effect"

    return EffectSizeResult(
        value=float(nnt),
        interpretation=interpretation,
        metric_name="NNT",
    )
