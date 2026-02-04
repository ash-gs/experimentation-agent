"""Power analysis utilities for AB testing experiment design."""

import math
from typing import Literal

from scipy import stats
from statsmodels.stats.power import NormalIndPower, TTestIndPower


def calculate_sample_size(
    baseline_rate: float,
    mde: float,
    power: float = 0.8,
    alpha: float = 0.05,
    ratio: float = 1.0,
    alternative: Literal["two-sided", "larger", "smaller"] = "two-sided",
) -> int:
    """Calculate required sample size per variant for a proportion test."""
    if not 0 < baseline_rate < 1:
        raise ValueError("baseline_rate must be between 0 and 1")
    if mde <= 0:
        raise ValueError("mde must be positive")
    if not 0 < power < 1:
        raise ValueError("power must be between 0 and 1")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")

    p1 = baseline_rate
    p2 = baseline_rate + mde

    if not 0 < p2 < 1:
        raise ValueError(f"baseline_rate + mde must be between 0 and 1, got {p2}")

    effect_size = 2 * (math.asin(math.sqrt(p2)) - math.asin(math.sqrt(p1)))

    analysis = NormalIndPower()
    sample_size = analysis.solve_power(
        effect_size=abs(effect_size),
        power=power,
        alpha=alpha,
        ratio=ratio,
        alternative=alternative,
    )
    return math.ceil(sample_size)


def calculate_sample_size_continuous(
    baseline_mean: float,
    baseline_std: float,
    mde: float,
    power: float = 0.8,
    alpha: float = 0.05,
    ratio: float = 1.0,
    alternative: Literal["two-sided", "larger", "smaller"] = "two-sided",
) -> int:
    """Calculate required sample size per variant for a continuous metric."""
    if baseline_std <= 0:
        raise ValueError("baseline_std must be positive")
    if mde <= 0:
        raise ValueError("mde must be positive")

    effect_size = mde / baseline_std

    analysis = TTestIndPower()
    sample_size = analysis.solve_power(
        effect_size=abs(effect_size),
        power=power,
        alpha=alpha,
        ratio=ratio,
        alternative=alternative,
    )
    return math.ceil(sample_size)


def calculate_power(
    n: int,
    baseline_rate: float,
    mde: float,
    alpha: float = 0.05,
    ratio: float = 1.0,
    alternative: Literal["two-sided", "larger", "smaller"] = "two-sided",
) -> float:
    """Calculate statistical power for given sample size and effect."""
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0 < baseline_rate < 1:
        raise ValueError("baseline_rate must be between 0 and 1")

    p1 = baseline_rate
    p2 = baseline_rate + mde

    if not 0 < p2 < 1:
        raise ValueError(f"baseline_rate + mde must be between 0 and 1, got {p2}")

    effect_size = 2 * (math.asin(math.sqrt(p2)) - math.asin(math.sqrt(p1)))

    analysis = NormalIndPower()
    power = analysis.solve_power(
        effect_size=abs(effect_size),
        nobs1=n,
        alpha=alpha,
        ratio=ratio,
        alternative=alternative,
    )
    return float(power)


def calculate_mde(
    n: int,
    baseline_rate: float,
    power: float = 0.8,
    alpha: float = 0.05,
    ratio: float = 1.0,
    alternative: Literal["two-sided", "larger", "smaller"] = "two-sided",
) -> float:
    """Calculate minimum detectable effect for given sample size and power."""
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0 < baseline_rate < 1:
        raise ValueError("baseline_rate must be between 0 and 1")

    analysis = NormalIndPower()
    effect_size = analysis.solve_power(
        nobs1=n,
        power=power,
        alpha=alpha,
        ratio=ratio,
        alternative=alternative,
    )

    arcsin_p1 = math.asin(math.sqrt(baseline_rate))
    arcsin_p2 = effect_size / 2 + arcsin_p1

    if arcsin_p2 > math.pi / 2:
        arcsin_p2 = math.pi / 2 - 0.001
    if arcsin_p2 < 0:
        arcsin_p2 = 0.001

    p2 = math.sin(arcsin_p2) ** 2
    mde = p2 - baseline_rate
    return abs(mde)


def estimate_duration(
    sample_size_per_variant: int,
    daily_traffic: int,
    num_variants: int = 2,
    traffic_allocation: float = 1.0,
) -> int:
    """Estimate experiment duration in days."""
    if sample_size_per_variant <= 0:
        raise ValueError("sample_size_per_variant must be positive")
    if daily_traffic <= 0:
        raise ValueError("daily_traffic must be positive")
    if num_variants < 2:
        raise ValueError("num_variants must be at least 2")
    if not 0 < traffic_allocation <= 1:
        raise ValueError("traffic_allocation must be between 0 and 1")

    total_sample_needed = sample_size_per_variant * num_variants
    effective_daily_traffic = daily_traffic * traffic_allocation
    duration = total_sample_needed / effective_daily_traffic
    return math.ceil(duration)


def power_curve(
    baseline_rate: float,
    mde: float,
    alpha: float = 0.05,
    sample_sizes: list[int] | None = None,
) -> list[tuple[int, float]]:
    """Generate power curve data for visualization."""
    if sample_sizes is None:
        min_n = calculate_sample_size(baseline_rate, mde, power=0.5, alpha=alpha)
        max_n = calculate_sample_size(baseline_rate, mde, power=0.99, alpha=alpha)
        sample_sizes = [int(min_n + (max_n - min_n) * i / 10) for i in range(11)]

    results = []
    for n in sample_sizes:
        power = calculate_power(n, baseline_rate, mde, alpha)
        results.append((n, power))
    return results
