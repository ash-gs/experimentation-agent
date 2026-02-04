"""Custom exceptions for the application."""


class ABTestingAgentError(Exception):
    """Base exception for all application errors."""

    pass


class ConfigurationError(ABTestingAgentError):
    """Configuration-related errors."""

    pass


class DataError(ABTestingAgentError):
    """Data-related errors (validation, missing data, etc.)."""

    pass


class StatisticalError(ABTestingAgentError):
    """Statistical calculation errors."""

    pass


class AgentError(ABTestingAgentError):
    """Agent execution errors."""

    pass


class LLMError(AgentError):
    """LLM-related errors."""

    pass


class DatabaseError(ABTestingAgentError):
    """Database operation errors."""

    pass
