"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    mock_response = Mock()
    mock_response.content = """
**Primary Hypothesis:**
"Changing the checkout button color from green to red will increase conversion rate by 0.5 percentage points."

**Metric:** Conversion Rate
**Expected Direction:** Increase
**Expected Effect Size:** 0.5 percentage points

**Rationale:**
Red buttons create urgency and may increase conversions.
"""
    return mock_response


@pytest.fixture
def sample_business_goal():
    """Sample business goal for testing."""
    return "I want to increase checkout conversions on our e-commerce site"
