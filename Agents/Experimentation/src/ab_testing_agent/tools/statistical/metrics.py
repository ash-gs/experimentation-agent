"""Metric aggregation and data quality utilities for AB testing."""

from typing import NamedTuple

import numpy as np
import pandas as pd
from scipy import stats


class ConversionMetric(NamedTuple):
    """Conversion metric aggregation result."""
    successes: int
    total: int
    rate: float
    variant_name: str


class ContinuousMetric(NamedTuple):
    """Continuous metric aggregation result."""
    mean: float
    std: float
    count: int
    values: np.ndarray
    variant_name: str


class SRMResult(NamedTuple):
    """Sample Ratio Mismatch detection result."""
    is_srm_detected: bool
    p_value: float
    expected_ratio: float
    observed_ratio: float
    control_n: int
    treatment_n: int
    message: str


def aggregate_conversion_rate(
    events: pd.DataFrame,
    variant_name: str,
    user_col: str = "user_id",
    variant_col: str = "variant_name",
    event_type_col: str = "event_type",
    exposure_event: str = "exposure",
    conversion_event: str = "conversion",
) -> ConversionMetric:
    """Aggregate conversion rate for a variant."""
    variant_events = events[events[variant_col] == variant_name]

    exposed_users = variant_events[variant_events[event_type_col] == exposure_event][
        user_col
    ].unique()
    total = len(exposed_users)

    converted_users = variant_events[
        variant_events[event_type_col] == conversion_event
    ][user_col].unique()

    successes = len(set(converted_users) & set(exposed_users))
    rate = successes / total if total > 0 else 0.0

    return ConversionMetric(
        successes=successes,
        total=total,
        rate=rate,
        variant_name=variant_name,
    )


def aggregate_continuous_metric(
    events: pd.DataFrame,
    variant_name: str,
    metric_col: str = "metric_value",
    user_col: str = "user_id",
    variant_col: str = "variant_name",
    event_type_col: str = "event_type",
    metric_event: str | None = None,
    aggregation: str = "mean",
) -> ContinuousMetric:
    """Aggregate continuous metric for a variant."""
    variant_events = events[events[variant_col] == variant_name]

    if metric_event:
        variant_events = variant_events[variant_events[event_type_col] == metric_event]

    variant_events = variant_events[variant_events[metric_col].notna()]

    if len(variant_events) == 0:
        return ContinuousMetric(
            mean=0.0,
            std=0.0,
            count=0,
            values=np.array([]),
            variant_name=variant_name,
        )

    agg_func = {"mean": "mean", "sum": "sum", "max": "max", "min": "min"}.get(
        aggregation, "mean"
    )
    user_values = variant_events.groupby(user_col)[metric_col].agg(agg_func)

    values = user_values.values
    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    count = len(values)

    return ContinuousMetric(
        mean=mean,
        std=std,
        count=count,
        values=np.array(values),
        variant_name=variant_name,
    )


def detect_sample_ratio_mismatch(
    control_n: int,
    treatment_n: int,
    expected_ratio: float = 0.5,
    alpha: float = 0.01,
) -> SRMResult:
    """Detect Sample Ratio Mismatch (SRM)."""
    total = control_n + treatment_n
    if total == 0:
        return SRMResult(
            is_srm_detected=False,
            p_value=1.0,
            expected_ratio=expected_ratio,
            observed_ratio=0.0,
            control_n=control_n,
            treatment_n=treatment_n,
            message="No samples to analyze",
        )

    observed_ratio = control_n / total
    expected_control = total * expected_ratio
    expected_treatment = total * (1 - expected_ratio)

    observed = np.array([control_n, treatment_n])
    expected = np.array([expected_control, expected_treatment])

    chi2, p_value = stats.chisquare(observed, expected)
    is_srm = p_value < alpha

    if is_srm:
        message = (
            f"SRM DETECTED: Expected {expected_ratio:.1%}/{1-expected_ratio:.1%} split, "
            f"observed {observed_ratio:.1%}/{1-observed_ratio:.1%}. "
            f"This may indicate randomization or data collection issues."
        )
    else:
        message = (
            f"No SRM detected. Observed split ({observed_ratio:.1%}/{1-observed_ratio:.1%}) "
            f"is consistent with expected ({expected_ratio:.1%}/{1-expected_ratio:.1%})."
        )

    return SRMResult(
        is_srm_detected=is_srm,
        p_value=float(p_value),
        expected_ratio=expected_ratio,
        observed_ratio=observed_ratio,
        control_n=control_n,
        treatment_n=treatment_n,
        message=message,
    )


def get_variant_sample_sizes(
    events: pd.DataFrame,
    user_col: str = "user_id",
    variant_col: str = "variant_name",
    event_type_col: str = "event_type",
    exposure_event: str = "exposure",
) -> dict[str, int]:
    """Get unique user counts per variant."""
    exposure_events = events[events[event_type_col] == exposure_event]
    return exposure_events.groupby(variant_col)[user_col].nunique().to_dict()


def calculate_experiment_summary(
    events: pd.DataFrame,
    control_name: str = "control",
    treatment_name: str = "treatment",
    user_col: str = "user_id",
    variant_col: str = "variant_name",
    event_type_col: str = "event_type",
    timestamp_col: str = "event_timestamp",
) -> dict:
    """Calculate summary statistics for an experiment."""
    min_date = pd.to_datetime(events[timestamp_col].min())
    max_date = pd.to_datetime(events[timestamp_col].max())
    duration = (max_date - min_date).days + 1

    sizes = get_variant_sample_sizes(events, user_col, variant_col, event_type_col)

    control_n = sizes.get(control_name, 0)
    treatment_n = sizes.get(treatment_name, 0)
    total_users = control_n + treatment_n

    srm = detect_sample_ratio_mismatch(control_n, treatment_n)

    total_events = len(events)
    event_types = events[event_type_col].value_counts().to_dict()

    return {
        "start_date": min_date.isoformat(),
        "end_date": max_date.isoformat(),
        "duration_days": duration,
        "total_users": total_users,
        "control_users": control_n,
        "treatment_users": treatment_n,
        "total_events": total_events,
        "event_types": event_types,
        "srm_detected": srm.is_srm_detected,
        "srm_p_value": srm.p_value,
        "variants": list(sizes.keys()),
    }


def validate_experiment_data(
    events: pd.DataFrame,
    required_columns: list[str] | None = None,
    min_sample_size: int = 100,
    control_name: str = "control",
    treatment_name: str = "treatment",
) -> tuple[bool, list[str]]:
    """Validate experiment data for analysis."""
    issues = []

    if required_columns is None:
        required_columns = ["user_id", "variant_name", "event_type", "event_timestamp"]

    missing_cols = [col for col in required_columns if col not in events.columns]
    if missing_cols:
        issues.append(f"Missing required columns: {missing_cols}")

    if issues:
        return False, issues

    if len(events) == 0:
        issues.append("No events in dataset")
        return False, issues

    sizes = get_variant_sample_sizes(events)

    if control_name not in sizes:
        issues.append(f"Control variant '{control_name}' not found")
    elif sizes[control_name] < min_sample_size:
        issues.append(
            f"Control sample size ({sizes[control_name]}) below minimum ({min_sample_size})"
        )

    if treatment_name not in sizes:
        issues.append(f"Treatment variant '{treatment_name}' not found")
    elif sizes[treatment_name] < min_sample_size:
        issues.append(
            f"Treatment sample size ({sizes[treatment_name]}) below minimum ({min_sample_size})"
        )

    for col in ["user_id", "variant_name"]:
        null_count = events[col].isna().sum()
        if null_count > 0:
            issues.append(f"Column '{col}' has {null_count} null values")

    if control_name in sizes and treatment_name in sizes:
        srm = detect_sample_ratio_mismatch(sizes[control_name], sizes[treatment_name])
        if srm.is_srm_detected:
            issues.append(f"Sample Ratio Mismatch detected (p={srm.p_value:.4f})")

    is_valid = len(issues) == 0
    return is_valid, issues
