"""Tests for metrics module."""

import numpy as np
import pandas as pd
import pytest

from ab_testing_agent.tools.statistical.metrics import (
    ContinuousMetric,
    ConversionMetric,
    SRMResult,
    aggregate_continuous_metric,
    aggregate_conversion_rate,
    calculate_experiment_summary,
    detect_sample_ratio_mismatch,
    get_variant_sample_sizes,
    validate_experiment_data,
)


@pytest.fixture
def sample_events():
    """Create sample experiment events DataFrame."""
    np.random.seed(42)

    # 1000 users per variant
    n_per_variant = 1000
    control_users = [f"user_{i}" for i in range(n_per_variant)]
    treatment_users = [f"user_{i}" for i in range(n_per_variant, 2 * n_per_variant)]

    events = []

    # Control exposure events
    for user_id in control_users:
        events.append(
            {
                "user_id": user_id,
                "variant_name": "control",
                "event_type": "exposure",
                "event_timestamp": "2024-01-01 10:00:00",
                "metric_value": None,
            }
        )

    # Treatment exposure events
    for user_id in treatment_users:
        events.append(
            {
                "user_id": user_id,
                "variant_name": "treatment",
                "event_type": "exposure",
                "event_timestamp": "2024-01-01 10:00:00",
                "metric_value": None,
            }
        )

    # Control conversions (5% rate = 50 users)
    for user_id in control_users[:50]:
        events.append(
            {
                "user_id": user_id,
                "variant_name": "control",
                "event_type": "conversion",
                "event_timestamp": "2024-01-01 11:00:00",
                "metric_value": np.random.uniform(10, 100),
            }
        )

    # Treatment conversions (6% rate = 60 users)
    for user_id in treatment_users[:60]:
        events.append(
            {
                "user_id": user_id,
                "variant_name": "treatment",
                "event_type": "conversion",
                "event_timestamp": "2024-01-01 11:00:00",
                "metric_value": np.random.uniform(15, 110),
            }
        )

    return pd.DataFrame(events)


class TestAggregateConversionRate:
    """Tests for aggregate_conversion_rate function."""

    def test_control_conversion_rate(self, sample_events):
        """Test control variant aggregation."""
        result = aggregate_conversion_rate(sample_events, "control")

        assert isinstance(result, ConversionMetric)
        assert result.variant_name == "control"
        assert result.total == 1000
        assert result.successes == 50
        assert result.rate == pytest.approx(0.05, rel=0.01)

    def test_treatment_conversion_rate(self, sample_events):
        """Test treatment variant aggregation."""
        result = aggregate_conversion_rate(sample_events, "treatment")

        assert result.variant_name == "treatment"
        assert result.total == 1000
        assert result.successes == 60
        assert result.rate == pytest.approx(0.06, rel=0.01)

    def test_nonexistent_variant(self, sample_events):
        """Test with variant that doesn't exist."""
        result = aggregate_conversion_rate(sample_events, "nonexistent")

        assert result.total == 0
        assert result.successes == 0
        assert result.rate == 0.0


class TestAggregateContinuousMetric:
    """Tests for aggregate_continuous_metric function."""

    def test_basic_aggregation(self, sample_events):
        """Test basic continuous metric aggregation."""
        result = aggregate_continuous_metric(
            sample_events,
            "control",
            metric_col="metric_value",
            metric_event="conversion",
        )

        assert isinstance(result, ContinuousMetric)
        assert result.variant_name == "control"
        assert result.count == 50  # 50 conversion events
        assert result.mean > 0
        assert result.std > 0

    def test_mean_difference(self, sample_events):
        """Test that treatment has higher mean."""
        control = aggregate_continuous_metric(
            sample_events, "control", metric_event="conversion"
        )
        treatment = aggregate_continuous_metric(
            sample_events, "treatment", metric_event="conversion"
        )

        # Treatment was generated with higher values
        assert treatment.mean > control.mean


class TestDetectSampleRatioMismatch:
    """Tests for detect_sample_ratio_mismatch function."""

    def test_no_srm_balanced(self):
        """Test no SRM with balanced traffic."""
        result = detect_sample_ratio_mismatch(
            control_n=50000, treatment_n=50000, expected_ratio=0.5
        )

        assert isinstance(result, SRMResult)
        assert not result.is_srm_detected
        assert result.p_value > 0.01

    def test_srm_detected(self):
        """Test SRM detection with imbalanced traffic."""
        result = detect_sample_ratio_mismatch(
            control_n=55000, treatment_n=45000, expected_ratio=0.5
        )

        assert result.is_srm_detected
        assert result.p_value < 0.01
        assert "SRM DETECTED" in result.message

    def test_slight_imbalance_ok(self):
        """Test slight imbalance is acceptable with smaller samples."""
        # With smaller samples, minor imbalance won't be statistically significant
        result = detect_sample_ratio_mismatch(
            control_n=510, treatment_n=490, expected_ratio=0.5
        )

        # Slight imbalance should not trigger SRM with smaller N
        assert not result.is_srm_detected

    def test_non_50_50_split(self):
        """Test with non-equal expected split."""
        result = detect_sample_ratio_mismatch(
            control_n=30000, treatment_n=70000, expected_ratio=0.3
        )

        # This matches 30/70 split
        assert not result.is_srm_detected

    def test_empty_data(self):
        """Test with no samples."""
        result = detect_sample_ratio_mismatch(control_n=0, treatment_n=0)

        assert not result.is_srm_detected
        assert result.message == "No samples to analyze"


class TestGetVariantSampleSizes:
    """Tests for get_variant_sample_sizes function."""

    def test_returns_correct_sizes(self, sample_events):
        """Test correct sample sizes returned."""
        sizes = get_variant_sample_sizes(sample_events)

        assert sizes["control"] == 1000
        assert sizes["treatment"] == 1000


class TestCalculateExperimentSummary:
    """Tests for calculate_experiment_summary function."""

    def test_summary_contents(self, sample_events):
        """Test summary contains expected keys."""
        summary = calculate_experiment_summary(sample_events)

        assert "start_date" in summary
        assert "end_date" in summary
        assert "duration_days" in summary
        assert "total_users" in summary
        assert "control_users" in summary
        assert "treatment_users" in summary
        assert "srm_detected" in summary

    def test_summary_values(self, sample_events):
        """Test summary values are correct."""
        summary = calculate_experiment_summary(sample_events)

        assert summary["total_users"] == 2000
        assert summary["control_users"] == 1000
        assert summary["treatment_users"] == 1000
        assert not summary["srm_detected"]


class TestValidateExperimentData:
    """Tests for validate_experiment_data function."""

    def test_valid_data(self, sample_events):
        """Test validation passes for valid data."""
        is_valid, issues = validate_experiment_data(sample_events)

        assert is_valid
        assert len(issues) == 0

    def test_missing_columns(self):
        """Test detection of missing columns."""
        df = pd.DataFrame({"user_id": [1, 2, 3]})

        is_valid, issues = validate_experiment_data(df)

        assert not is_valid
        assert any("Missing required columns" in issue for issue in issues)

    def test_small_sample_size(self, sample_events):
        """Test detection of small sample size."""
        small_events = sample_events.head(50)  # Very few events

        is_valid, issues = validate_experiment_data(
            small_events, min_sample_size=1000
        )

        assert not is_valid
        assert any("below minimum" in issue for issue in issues)

    def test_srm_warning(self):
        """Test SRM warning in validation."""
        # Create imbalanced data
        events = []
        for i in range(1000):
            events.append(
                {
                    "user_id": f"user_{i}",
                    "variant_name": "control",
                    "event_type": "exposure",
                    "event_timestamp": "2024-01-01",
                }
            )
        for i in range(500):  # Only half as many in treatment
            events.append(
                {
                    "user_id": f"user_{1000 + i}",
                    "variant_name": "treatment",
                    "event_type": "exposure",
                    "event_timestamp": "2024-01-01",
                }
            )

        df = pd.DataFrame(events)
        is_valid, issues = validate_experiment_data(df, min_sample_size=100)

        assert any("Sample Ratio Mismatch" in issue for issue in issues)
