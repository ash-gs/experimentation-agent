"""Tests for confidence intervals module."""

import numpy as np
import pytest

from testing_agent.tools.statistical.confidence_intervals import (
    ConfidenceInterval,
    difference_confidence_interval_means,
    difference_confidence_interval_proportions,
    mean_confidence_interval,
    proportion_confidence_interval,
    relative_difference_confidence_interval,
)


class TestMeanConfidenceInterval:
    """Tests for mean_confidence_interval function."""

    def test_known_distribution(self):
        """Test with known normal distribution."""
        np.random.seed(42)
        data = np.random.normal(100, 10, 1000)

        ci = mean_confidence_interval(data, confidence=0.95)

        # Mean should be close to 100
        assert 99 < ci.point_estimate < 101
        # CI should contain true mean
        assert ci.lower < 100 < ci.upper

    def test_returns_named_tuple(self):
        """Test return type."""
        data = [1, 2, 3, 4, 5]
        ci = mean_confidence_interval(data)

        assert isinstance(ci, ConfidenceInterval)
        assert hasattr(ci, "point_estimate")
        assert hasattr(ci, "lower")
        assert hasattr(ci, "upper")
        assert hasattr(ci, "confidence_level")

    def test_higher_confidence_wider_interval(self):
        """Higher confidence should give wider intervals."""
        data = list(range(100))

        ci_95 = mean_confidence_interval(data, confidence=0.95)
        ci_99 = mean_confidence_interval(data, confidence=0.99)

        width_95 = ci_95.upper - ci_95.lower
        width_99 = ci_99.upper - ci_99.lower

        assert width_99 > width_95

    def test_larger_sample_narrower_interval(self):
        """Larger samples should give narrower intervals."""
        np.random.seed(42)
        small_sample = np.random.normal(50, 10, 30)
        large_sample = np.random.normal(50, 10, 1000)

        ci_small = mean_confidence_interval(small_sample)
        ci_large = mean_confidence_interval(large_sample)

        width_small = ci_small.upper - ci_small.lower
        width_large = ci_large.upper - ci_large.lower

        assert width_large < width_small

    def test_minimum_samples(self):
        """Test error with insufficient samples."""
        with pytest.raises(ValueError, match="at least 2"):
            mean_confidence_interval([1])


class TestProportionConfidenceInterval:
    """Tests for proportion_confidence_interval function."""

    def test_known_proportion(self):
        """Test with known proportion."""
        # 50% proportion with large sample
        ci = proportion_confidence_interval(successes=500, total=1000, confidence=0.95)

        assert ci.point_estimate == 0.5
        # CI should contain true value
        assert ci.lower < 0.5 < ci.upper

    def test_small_proportion(self):
        """Test with small proportion (5%)."""
        ci = proportion_confidence_interval(successes=50, total=1000, confidence=0.95)

        assert ci.point_estimate == 0.05
        assert ci.lower < 0.05 < ci.upper

    def test_boundary_proportions(self):
        """Test edge cases."""
        # All successes
        ci_all = proportion_confidence_interval(successes=100, total=100)
        assert ci_all.point_estimate == 1.0

        # No successes
        ci_none = proportion_confidence_interval(successes=0, total=100)
        assert ci_none.point_estimate == 0.0

    def test_validation(self):
        """Test input validation."""
        with pytest.raises(ValueError):
            proportion_confidence_interval(successes=-1, total=100)
        with pytest.raises(ValueError):
            proportion_confidence_interval(successes=101, total=100)
        with pytest.raises(ValueError):
            proportion_confidence_interval(successes=50, total=0)


class TestDifferenceConfidenceIntervalProportions:
    """Tests for difference_confidence_interval_proportions function."""

    def test_significant_difference(self):
        """Test CI for significant difference."""
        ci = difference_confidence_interval_proportions(
            control_successes=500,
            control_total=10000,  # 5%
            treatment_successes=600,
            treatment_total=10000,  # 6%
            confidence=0.95,
        )

        # True difference is 1pp
        assert ci.point_estimate == pytest.approx(0.01, rel=0.01)
        # CI should not include zero for significant difference
        assert ci.lower > 0 or ci.upper < 0

    def test_non_significant_difference(self):
        """Test CI for non-significant difference."""
        ci = difference_confidence_interval_proportions(
            control_successes=500,
            control_total=10000,  # 5%
            treatment_successes=505,
            treatment_total=10000,  # 5.05%
            confidence=0.95,
        )

        # CI should include zero for tiny difference
        assert ci.lower < 0 < ci.upper

    def test_symmetric_around_estimate(self):
        """CI should be approximately symmetric around point estimate."""
        ci = difference_confidence_interval_proportions(
            control_successes=500,
            control_total=10000,
            treatment_successes=550,
            treatment_total=10000,
        )

        lower_dist = ci.point_estimate - ci.lower
        upper_dist = ci.upper - ci.point_estimate

        assert lower_dist == pytest.approx(upper_dist, rel=0.1)


class TestDifferenceConfidenceIntervalMeans:
    """Tests for difference_confidence_interval_means function."""

    def test_significant_difference(self):
        """Test CI for significant mean difference."""
        np.random.seed(42)
        control = np.random.normal(10, 2, 100)
        treatment = np.random.normal(15, 2, 100)  # 5 unit difference

        ci = difference_confidence_interval_means(control, treatment)

        # Should not include zero
        assert ci.lower > 0
        assert ci.point_estimate == pytest.approx(5.0, rel=0.2)

    def test_welch_vs_pooled(self):
        """Test Welch vs pooled variance assumption."""
        np.random.seed(42)
        control = np.random.normal(10, 2, 50)
        treatment = np.random.normal(10, 5, 50)  # Same mean, different variance

        ci_welch = difference_confidence_interval_means(
            control, treatment, equal_var=False
        )
        ci_pooled = difference_confidence_interval_means(
            control, treatment, equal_var=True
        )

        # Both should include zero (no difference)
        assert ci_welch.lower < 0 < ci_welch.upper
        assert ci_pooled.lower < 0 < ci_pooled.upper


class TestRelativeDifferenceConfidenceInterval:
    """Tests for relative_difference_confidence_interval function."""

    def test_10_percent_lift(self):
        """Test CI for 10% relative lift."""
        ci = relative_difference_confidence_interval(
            control_successes=500,
            control_total=10000,  # 5%
            treatment_successes=550,
            treatment_total=10000,  # 5.5%
        )

        # 10% lift
        assert ci.point_estimate == pytest.approx(0.10, rel=0.01)

    def test_negative_lift(self):
        """Test CI for negative lift."""
        ci = relative_difference_confidence_interval(
            control_successes=600,
            control_total=10000,  # 6%
            treatment_successes=500,
            treatment_total=10000,  # 5%
        )

        # Should be negative
        assert ci.point_estimate < 0

    def test_zero_control_rate_error(self):
        """Test error when control rate is zero."""
        with pytest.raises(ValueError, match="control rate must be positive"):
            relative_difference_confidence_interval(
                control_successes=0,
                control_total=10000,
                treatment_successes=100,
                treatment_total=10000,
            )
