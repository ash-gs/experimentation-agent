"""Confidence interval calculations for AB testing."""

import math
from typing import NamedTuple

import numpy as np
from scipy import stats
from statsmodels.stats.proportion import proportion_confint


class ConfidenceInterval(NamedTuple):
    """Confidence interval result."""
    point_estimate: float
    lower: float
    upper: float
    confidence_level: float


def mean_confidence_interval(
    data: list[float] | np.ndarray,
    confidence: float = 0.95,
) -> ConfidenceInterval:
    """Calculate confidence interval for a sample mean."""
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")

    data = np.asarray(data)
    n = len(data)
    if n < 2:
        raise ValueError("Need at least 2 data points")

    mean = np.mean(data)
    std_err = stats.sem(data)
    alpha = 1 - confidence
    t_crit = stats.t.ppf(1 - alpha / 2, df=n - 1)
    margin = t_crit * std_err

    return ConfidenceInterval(
        point_estimate=float(mean),
        lower=float(mean - margin),
        upper=float(mean + margin),
        confidence_level=confidence,
    )


def proportion_confidence_interval(
    successes: int,
    total: int,
    confidence: float = 0.95,
    method: str = "wilson",
) -> ConfidenceInterval:
    """Calculate confidence interval for a proportion."""
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")
    if total <= 0:
        raise ValueError("total must be positive")
    if successes < 0 or successes > total:
        raise ValueError("successes must be between 0 and total")

    proportion = successes / total
    alpha = 1 - confidence
    lower, upper = proportion_confint(successes, total, alpha=alpha, method=method)

    return ConfidenceInterval(
        point_estimate=float(proportion),
        lower=float(lower),
        upper=float(upper),
        confidence_level=confidence,
    )


def difference_confidence_interval_proportions(
    control_successes: int,
    control_total: int,
    treatment_successes: int,
    treatment_total: int,
    confidence: float = 0.95,
) -> ConfidenceInterval:
    """Calculate CI for difference between two proportions."""
    if control_total <= 0 or treatment_total <= 0:
        raise ValueError("sample sizes must be positive")

    p1 = control_successes / control_total
    p2 = treatment_successes / treatment_total
    diff = p2 - p1

    se = math.sqrt(p1 * (1 - p1) / control_total + p2 * (1 - p2) / treatment_total)
    alpha = 1 - confidence
    z_crit = stats.norm.ppf(1 - alpha / 2)
    margin = z_crit * se

    return ConfidenceInterval(
        point_estimate=float(diff),
        lower=float(diff - margin),
        upper=float(diff + margin),
        confidence_level=confidence,
    )


def difference_confidence_interval_means(
    control_data: list[float] | np.ndarray,
    treatment_data: list[float] | np.ndarray,
    confidence: float = 0.95,
    equal_var: bool = False,
) -> ConfidenceInterval:
    """Calculate CI for difference between two means."""
    control = np.asarray(control_data)
    treatment = np.asarray(treatment_data)

    n1, n2 = len(control), len(treatment)
    if n1 < 2 or n2 < 2:
        raise ValueError("Need at least 2 data points per group")

    mean1, mean2 = np.mean(control), np.mean(treatment)
    var1, var2 = np.var(control, ddof=1), np.var(treatment, ddof=1)
    diff = mean2 - mean1

    if equal_var:
        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
        se = math.sqrt(pooled_var * (1 / n1 + 1 / n2))
        df = n1 + n2 - 2
    else:
        se = math.sqrt(var1 / n1 + var2 / n2)
        df = (var1 / n1 + var2 / n2) ** 2 / (
            (var1 / n1) ** 2 / (n1 - 1) + (var2 / n2) ** 2 / (n2 - 1)
        )

    alpha = 1 - confidence
    t_crit = stats.t.ppf(1 - alpha / 2, df=df)
    margin = t_crit * se

    return ConfidenceInterval(
        point_estimate=float(diff),
        lower=float(diff - margin),
        upper=float(diff + margin),
        confidence_level=confidence,
    )


def relative_difference_confidence_interval(
    control_successes: int,
    control_total: int,
    treatment_successes: int,
    treatment_total: int,
    confidence: float = 0.95,
) -> ConfidenceInterval:
    """Calculate CI for relative difference (lift) between proportions."""
    if control_total <= 0 or treatment_total <= 0:
        raise ValueError("sample sizes must be positive")

    p1 = control_successes / control_total
    p2 = treatment_successes / treatment_total

    if p1 <= 0:
        raise ValueError("control rate must be positive for relative lift")

    relative_lift = (p2 - p1) / p1
    var_p1 = p1 * (1 - p1) / control_total
    var_p2 = p2 * (1 - p2) / treatment_total
    se_lift = math.sqrt((1 / p1**2) * var_p2 + (p2 / p1**2) ** 2 * var_p1)

    alpha = 1 - confidence
    z_crit = stats.norm.ppf(1 - alpha / 2)
    margin = z_crit * se_lift

    return ConfidenceInterval(
        point_estimate=float(relative_lift),
        lower=float(relative_lift - margin),
        upper=float(relative_lift + margin),
        confidence_level=confidence,
    )
