"""Statistical hypothesis testing for AB experiments."""

import math
from typing import Literal

import numpy as np
from scipy import stats

from ...data.schemas import StatisticalTestResultSchema
from .confidence_intervals import (
    difference_confidence_interval_means,
    difference_confidence_interval_proportions,
)
from .effect_sizes import absolute_difference, cohens_d, cohens_h, relative_lift


def two_sample_ttest(
    control_data: list[float] | np.ndarray,
    treatment_data: list[float] | np.ndarray,
    alpha: float = 0.05,
    confidence_level: float = 0.95,
    equal_var: bool = False,
    alternative: Literal["two-sided", "greater", "less"] = "two-sided",
) -> StatisticalTestResultSchema:
    """Perform two-sample t-test for continuous metrics."""
    control = np.asarray(control_data)
    treatment = np.asarray(treatment_data)

    n1, n2 = len(control), len(treatment)
    if n1 < 2 or n2 < 2:
        raise ValueError("Need at least 2 data points per group")

    control_mean = float(np.mean(control))
    treatment_mean = float(np.mean(treatment))
    control_std = float(np.std(control, ddof=1))
    treatment_std = float(np.std(treatment, ddof=1))

    stat, p_value = stats.ttest_ind(
        treatment, control, equal_var=equal_var, alternative=alternative
    )

    ci = difference_confidence_interval_means(
        control, treatment, confidence=confidence_level, equal_var=equal_var
    )

    abs_diff = absolute_difference(control_mean, treatment_mean)
    d = cohens_d(control, treatment)
    lift = relative_lift(control_mean, treatment_mean) if control_mean != 0 else None

    return StatisticalTestResultSchema(
        test_type="two_sample_ttest" + ("" if not equal_var else "_equal_var"),
        control_mean=control_mean,
        treatment_mean=treatment_mean,
        control_std=control_std,
        treatment_std=treatment_std,
        control_n=n1,
        treatment_n=n2,
        statistic=float(stat),
        p_value=float(p_value),
        confidence_interval_lower=ci.lower,
        confidence_interval_upper=ci.upper,
        confidence_level=confidence_level,
        effect_size=abs_diff.value,
        relative_effect=lift.value if lift else None,
        statistically_significant=p_value < alpha,
        practical_significance=abs(d.value) >= 0.2,
    )


def two_proportion_ztest(
    control_successes: int,
    control_n: int,
    treatment_successes: int,
    treatment_n: int,
    alpha: float = 0.05,
    confidence_level: float = 0.95,
    alternative: Literal["two-sided", "larger", "smaller"] = "two-sided",
) -> StatisticalTestResultSchema:
    """Perform two-proportion z-test for conversion rates."""
    if control_n <= 0 or treatment_n <= 0:
        raise ValueError("Sample sizes must be positive")
    if control_successes < 0 or treatment_successes < 0:
        raise ValueError("Successes cannot be negative")
    if control_successes > control_n or treatment_successes > treatment_n:
        raise ValueError("Successes cannot exceed sample size")

    p1 = control_successes / control_n
    p2 = treatment_successes / treatment_n

    pooled_p = (control_successes + treatment_successes) / (control_n + treatment_n)
    pooled_se = math.sqrt(pooled_p * (1 - pooled_p) * (1 / control_n + 1 / treatment_n))

    if pooled_se == 0:
        z_stat = 0.0
        p_value = 1.0
    else:
        z_stat = (p2 - p1) / pooled_se
        if alternative == "two-sided":
            p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        elif alternative == "larger":
            p_value = 1 - stats.norm.cdf(z_stat)
        else:
            p_value = stats.norm.cdf(z_stat)

    ci = difference_confidence_interval_proportions(
        control_successes, control_n, treatment_successes, treatment_n,
        confidence=confidence_level,
    )

    abs_diff = p2 - p1
    h = cohens_h(p1, p2)
    lift = relative_lift(p1, p2) if p1 > 0 else None

    return StatisticalTestResultSchema(
        test_type="two_proportion_ztest",
        control_mean=p1,
        treatment_mean=p2,
        control_std=math.sqrt(p1 * (1 - p1)) if 0 < p1 < 1 else 0,
        treatment_std=math.sqrt(p2 * (1 - p2)) if 0 < p2 < 1 else 0,
        control_n=control_n,
        treatment_n=treatment_n,
        statistic=float(z_stat),
        p_value=float(p_value),
        confidence_interval_lower=ci.lower,
        confidence_interval_upper=ci.upper,
        confidence_level=confidence_level,
        effect_size=abs_diff,
        relative_effect=lift.value if lift else None,
        statistically_significant=p_value < alpha,
        practical_significance=abs(h.value) >= 0.2,
    )


def chi_square_test(
    control_successes: int,
    control_n: int,
    treatment_successes: int,
    treatment_n: int,
    alpha: float = 0.05,
    confidence_level: float = 0.95,
) -> StatisticalTestResultSchema:
    """Perform chi-square test for independence."""
    if control_n <= 0 or treatment_n <= 0:
        raise ValueError("Sample sizes must be positive")

    control_failures = control_n - control_successes
    treatment_failures = treatment_n - treatment_successes

    contingency_table = np.array([
        [control_failures, control_successes],
        [treatment_failures, treatment_successes],
    ])

    chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)

    p1 = control_successes / control_n
    p2 = treatment_successes / treatment_n

    ci = difference_confidence_interval_proportions(
        control_successes, control_n, treatment_successes, treatment_n,
        confidence=confidence_level,
    )

    abs_diff = p2 - p1
    h = cohens_h(p1, p2)
    lift = relative_lift(p1, p2) if p1 > 0 else None

    return StatisticalTestResultSchema(
        test_type="chi_square_test",
        control_mean=p1,
        treatment_mean=p2,
        control_std=math.sqrt(p1 * (1 - p1)) if 0 < p1 < 1 else 0,
        treatment_std=math.sqrt(p2 * (1 - p2)) if 0 < p2 < 1 else 0,
        control_n=control_n,
        treatment_n=treatment_n,
        statistic=float(chi2),
        p_value=float(p_value),
        confidence_interval_lower=ci.lower,
        confidence_interval_upper=ci.upper,
        confidence_level=confidence_level,
        effect_size=abs_diff,
        relative_effect=lift.value if lift else None,
        statistically_significant=p_value < alpha,
        practical_significance=abs(h.value) >= 0.2,
    )


def mann_whitney_u(
    control_data: list[float] | np.ndarray,
    treatment_data: list[float] | np.ndarray,
    alpha: float = 0.05,
    confidence_level: float = 0.95,
    alternative: Literal["two-sided", "greater", "less"] = "two-sided",
) -> StatisticalTestResultSchema:
    """Perform Mann-Whitney U test (non-parametric)."""
    control = np.asarray(control_data)
    treatment = np.asarray(treatment_data)

    n1, n2 = len(control), len(treatment)
    if n1 < 2 or n2 < 2:
        raise ValueError("Need at least 2 data points per group")

    stat, p_value = stats.mannwhitneyu(
        treatment, control, alternative=alternative, method="auto"
    )

    control_mean = float(np.median(control))
    treatment_mean = float(np.median(treatment))
    control_std = float(np.std(control, ddof=1))
    treatment_std = float(np.std(treatment, ddof=1))

    ci = difference_confidence_interval_means(
        control, treatment, confidence=confidence_level, equal_var=False
    )

    mean_control = float(np.mean(control))
    mean_treatment = float(np.mean(treatment))
    abs_diff = absolute_difference(mean_control, mean_treatment)
    d = cohens_d(control, treatment)
    lift = relative_lift(mean_control, mean_treatment) if mean_control != 0 else None

    return StatisticalTestResultSchema(
        test_type="mann_whitney_u",
        control_mean=control_mean,
        treatment_mean=treatment_mean,
        control_std=control_std,
        treatment_std=treatment_std,
        control_n=n1,
        treatment_n=n2,
        statistic=float(stat),
        p_value=float(p_value),
        confidence_interval_lower=ci.lower,
        confidence_interval_upper=ci.upper,
        confidence_level=confidence_level,
        effect_size=abs_diff.value,
        relative_effect=lift.value if lift else None,
        statistically_significant=p_value < alpha,
        practical_significance=abs(d.value) >= 0.2,
    )


def bootstrap_test(
    control_data: list[float] | np.ndarray,
    treatment_data: list[float] | np.ndarray,
    n_bootstrap: int = 10000,
    alpha: float = 0.05,
    confidence_level: float = 0.95,
    statistic: str = "mean",
    random_state: int | None = None,
) -> StatisticalTestResultSchema:
    """Perform bootstrap hypothesis test."""
    control = np.asarray(control_data)
    treatment = np.asarray(treatment_data)

    n1, n2 = len(control), len(treatment)
    if n1 < 2 or n2 < 2:
        raise ValueError("Need at least 2 data points per group")

    rng = np.random.default_rng(random_state)
    stat_func = np.mean if statistic == "mean" else np.median

    observed_diff = stat_func(treatment) - stat_func(control)
    pooled = np.concatenate([control, treatment])

    null_diffs = []
    for _ in range(n_bootstrap):
        perm = rng.permutation(pooled)
        null_diff = stat_func(perm[n1:]) - stat_func(perm[:n1])
        null_diffs.append(null_diff)

    null_diffs = np.array(null_diffs)
    p_value = np.mean(np.abs(null_diffs) >= np.abs(observed_diff))

    boot_diffs = []
    for _ in range(n_bootstrap):
        boot_control = rng.choice(control, size=n1, replace=True)
        boot_treatment = rng.choice(treatment, size=n2, replace=True)
        boot_diffs.append(stat_func(boot_treatment) - stat_func(boot_control))

    boot_diffs = np.array(boot_diffs)
    ci_lower = np.percentile(boot_diffs, (1 - confidence_level) / 2 * 100)
    ci_upper = np.percentile(boot_diffs, (1 + confidence_level) / 2 * 100)

    control_mean = float(stat_func(control))
    treatment_mean = float(stat_func(treatment))
    control_std = float(np.std(control, ddof=1))
    treatment_std = float(np.std(treatment, ddof=1))

    d = cohens_d(control, treatment)
    lift = (
        relative_lift(np.mean(control), np.mean(treatment))
        if np.mean(control) != 0
        else None
    )

    return StatisticalTestResultSchema(
        test_type=f"bootstrap_{statistic}",
        control_mean=control_mean,
        treatment_mean=treatment_mean,
        control_std=control_std,
        treatment_std=treatment_std,
        control_n=n1,
        treatment_n=n2,
        statistic=float(observed_diff),
        p_value=float(p_value),
        confidence_interval_lower=float(ci_lower),
        confidence_interval_upper=float(ci_upper),
        confidence_level=confidence_level,
        effect_size=float(observed_diff),
        relative_effect=lift.value if lift else None,
        statistically_significant=p_value < alpha,
        practical_significance=abs(d.value) >= 0.2,
    )
