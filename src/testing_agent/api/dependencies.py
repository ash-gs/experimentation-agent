"""Dependency injection for API routes."""

from ..agents.analysis import AnalysisAgent
from ..agents.decision import DecisionAgent
from ..agents.design import DesignAgent
from ..agents.hypothesis import HypothesisAgent


def get_hypothesis_agent() -> HypothesisAgent:
    """Get a fresh HypothesisAgent instance.

    Returns:
        HypothesisAgent: Initialized hypothesis agent
    """
    return HypothesisAgent()


def get_design_agent() -> DesignAgent:
    """Get a fresh DesignAgent instance.

    Returns:
        DesignAgent: Initialized design agent
    """
    return DesignAgent()


def get_analysis_agent() -> AnalysisAgent:
    """Get a fresh AnalysisAgent instance.

    Returns:
        AnalysisAgent: Initialized analysis agent
    """
    return AnalysisAgent()


def get_decision_agent() -> DecisionAgent:
    """Get a fresh DecisionAgent instance.

    Returns:
        DecisionAgent: Initialized decision agent
    """
    return DecisionAgent()
