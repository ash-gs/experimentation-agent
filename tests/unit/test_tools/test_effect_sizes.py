"""Tests for effect sizes module."""

import numpy as np
import pytest

from testing_agent.tools.statistical.effect_sizes import (
    EffectSizeResult,
    absolute_difference,
    cohens_d,
    cohens_h,
    number_needed_to_treat,
    odds_ratio,
    relative_lift,
    risk_ratio,
)


class TestCohensD:
    """Tests for cohens_d function."""

    def test_known_effect_size(self):
        """Test with known effect size."""
        # Control: mean=10, sd=5
        # Treatment: mean=12.5, sd=5
        # Cohen's d should be 0.5 (medium effect)
        np.random.seed(42)
        control = np.random.normal(10, 5, 1000)
        treatment = np.random.normal(12.5, 5, 1000)

        result = cohens_d(control, treatment)

        assert result.value == pytest.approx(0.5, rel=0.2)  # Allow 20% tolerance due to sampling
        assert result.interpretation == "medium"

    def test_small_effect(self):
        """Test small effect size."""
        np.random.seed(42)
        control = np.random.normal(10, 5, 1000)
        treatment = np.random.normal(11, 5, 1000)  # d ≈ 0.2

        result = cohens_d(control, treatment)

        assert 0.15 < abs(result.value) < 0.3
        assert result.interpretation == "small"

    def test_large_effect(self):
        """Test large effect size."""
        np.random.seed(42)
        control = np.random.normal(10, 5, 1000)
        treatment = np.random.normal(14, 5, 1000)  # d ≈ 0.8

        result = cohens_d(control, treatment)

        assert result.interpretation == "large"

    def test_negative_effect(self):
        """Test negative effect (treatment < control)."""
        control = [10, 11, 12, 13, 14]
        treatment = [5, 6, 7, 8, 9]

        result = cohens_d(control, treatment)

        assert result.value < 0

    def test_returns_named_tuple(self):
        """Test return type."""
        result = cohens_d([1, 2, 3], [4, 5, 6])

        assert isinstance(result, EffectSizeResult)
        assert result.metric_name == "Cohen's d"


class TestCohensH:
    """Tests for cohens_h function."""

    def test_known_effect_size(self):
        """Test with known proportions."""
        # 5% vs 10% (large effect)
        result = cohens_h(control_rate=0.05, treatment_rate=0.10)

        assert result.value > 0
        assert result.metric_name == "Cohen's h"

    def test_same_proportions(self):
        """Test when proportions are equal."""
        result = cohens_h(control_rate=0.5, treatment_rate=0.5)

        assert result.value == pytest.approx(0, abs=0.001)
        assert result.interpretation == "negligible"

    def test_small_lift(self):
        """Test small lift (5% -> 5.5%)."""
        result = cohens_h(control_rate=0.05, treatment_rate=0.055)

        # Should be small effect
        assert abs(result.value) < 0.2

    def test_validation(self):
        """Test input validation."""
        with pytest.raises(ValueError):
            cohens_h(control_rate=-0.1, treatment_rate=0.5)
        with pytest.raises(ValueError):
            cohens_h(control_rate=0.5, treatment_rate=1.5)


class TestRelativeLift:
    """Tests for relative_lift function."""

    def test_10_percent_lift(self):
        """Test 10% lift."""
        result = relative_lift(control_value=0.05, treatment_value=0.055)

        assert result.value == pytest.approx(10.0, rel=0.01)
        assert result.metric_name == "relative_lift_percent"

    def test_negative_lift(self):
        """Test negative lift."""
        result = relative_lift(control_value=0.10, treatment_value=0.08)

        assert result.value == pytest.approx(-20.0, rel=0.01)

    def test_zero_lift(self):
        """Test zero lift."""
        result = relative_lift(control_value=0.05, treatment_value=0.05)

        assert result.value == 0.0
        assert result.interpretation == "negligible"

    def test_zero_control_error(self):
        """Test error when control is zero."""
        with pytest.raises(ValueError, match="cannot be zero"):
            relative_lift(control_value=0, treatment_value=0.05)

    def test_interpretation(self):
        """Test lift interpretation."""
        small_lift = relative_lift(0.05, 0.052)  # 4%
        assert small_lift.interpretation == "small"

        large_lift = relative_lift(0.05, 0.06)  # 20%
        assert large_lift.interpretation == "large"


class TestAbsoluteDifference:
    """Tests for absolute_difference function."""

    def test_positive_difference(self):
        """Test positive difference."""
        result = absolute_difference(control_value=0.05, treatment_value=0.055)

        assert result.value == pytest.approx(0.005, rel=0.01)

    def test_negative_difference(self):
        """Test negative difference."""
        result = absolute_difference(control_value=0.10, treatment_value=0.08)

        assert result.value == pytest.approx(-0.02, rel=0.01)


class TestOddsRatio:
    """Tests for odds_ratio function."""

    def test_no_effect(self):
        """Test when odds ratio is 1."""
        result = odds_ratio(control_rate=0.5, treatment_rate=0.5)

        assert result.value == pytest.approx(1.0, rel=0.01)
        assert result.interpretation == "negligible"

    def test_positive_effect(self):
        """Test positive effect."""
        result = odds_ratio(control_rate=0.05, treatment_rate=0.10)

        assert result.value > 1  # Treatment increases odds

    def test_negative_effect(self):
        """Test negative effect."""
        result = odds_ratio(control_rate=0.10, treatment_rate=0.05)

        assert result.value < 1  # Treatment decreases odds

    def test_validation(self):
        """Test boundary validation."""
        with pytest.raises(ValueError):
            odds_ratio(control_rate=0, treatment_rate=0.5)
        with pytest.raises(ValueError):
            odds_ratio(control_rate=1.0, treatment_rate=0.5)


class TestRiskRatio:
    """Tests for risk_ratio function."""

    def test_no_effect(self):
        """Test when risk ratio is 1."""
        result = risk_ratio(control_rate=0.5, treatment_rate=0.5)

        assert result.value == pytest.approx(1.0, rel=0.01)

    def test_doubled_risk(self):
        """Test doubled risk."""
        result = risk_ratio(control_rate=0.05, treatment_rate=0.10)

        assert result.value == pytest.approx(2.0, rel=0.01)

    def test_halved_risk(self):
        """Test halved risk."""
        result = risk_ratio(control_rate=0.10, treatment_rate=0.05)

        assert result.value == pytest.approx(0.5, rel=0.01)


class TestNumberNeededToTreat:
    """Tests for number_needed_to_treat function."""

    def test_nnt_calculation(self):
        """Test NNT calculation."""
        # 5% -> 5.5% = 0.5pp difference, NNT = 200
        result = number_needed_to_treat(control_rate=0.05, treatment_rate=0.055)

        assert result.value == pytest.approx(200, rel=0.01)

    def test_large_effect(self):
        """Test NNT for large effect."""
        # 5% -> 15% = 10pp difference, NNT = 10
        result = number_needed_to_treat(control_rate=0.05, treatment_rate=0.15)

        assert result.value == pytest.approx(10, rel=0.01)
        assert result.interpretation == "very strong effect"

    def test_no_effect(self):
        """Test NNT when no difference."""
        result = number_needed_to_treat(control_rate=0.05, treatment_rate=0.05)

        assert result.value == float("inf")
        assert result.interpretation == "no effect"
