"""Tests for Hypothesis Agent."""

import pytest
from unittest.mock import Mock, patch

from ab_testing_agent.agents.hypothesis import HypothesisAgent, HypothesisOutput
from ab_testing_agent.data.schemas import Direction


class TestHypothesisAgent:
    """Tests for HypothesisAgent."""

    @pytest.fixture
    def agent(self):
        """Create a hypothesis agent for testing."""
        # Mock the API key check
        with patch("ab_testing_agent.agents.base.settings.anthropic_api_key", "test-key"):
            return HypothesisAgent()

    def test_agent_initialization(self, agent):
        """Test that agent initializes correctly."""
        assert agent is not None
        assert agent.model_name is not None
        assert len(agent.messages) == 0

    def test_system_prompt_loaded(self, agent):
        """Test that system prompt is loaded."""
        prompt = agent.get_system_prompt()
        assert len(prompt) > 0
        assert "hypothesis" in prompt.lower()

    @patch("ab_testing_agent.agents.base.ChatAnthropic")
    def test_generate_hypothesis_structured(self, mock_claude, agent):
        """Test structured hypothesis generation."""
        # Mock structured LLM response
        mock_output = HypothesisOutput(
            hypothesis_description="Changing button color will increase conversion by 0.5pp",
            primary_metric="conversion_rate",
            expected_direction=Direction.INCREASE,
            expected_effect_size=0.005,
            rationale="Red buttons create urgency",
            is_testable=True,
            is_specific=True,
            is_measurable=True,
        )

        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = mock_output
        agent.llm.with_structured_output = Mock(return_value=mock_structured_llm)

        # Generate hypothesis
        hypothesis = agent.generate_hypothesis("Increase checkout conversions")

        # Verify
        assert hypothesis.description == mock_output.hypothesis_description
        assert hypothesis.metric == mock_output.primary_metric
        assert hypothesis.expected_direction == Direction.INCREASE
        assert hypothesis.expected_effect_size == 0.005

    def test_clear_history(self, agent):
        """Test clearing conversation history."""
        agent.messages.append(Mock())
        agent.messages.append(Mock())
        assert len(agent.messages) == 2

        agent.clear_history()
        assert len(agent.messages) == 0
