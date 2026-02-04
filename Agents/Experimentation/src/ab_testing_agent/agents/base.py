"""Base agent class for LLM-powered agents."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

from ..config.settings import settings
from ..utils.exceptions import LLMError
from ..utils.logging import get_logger

T = TypeVar("T", bound=BaseModel)

logger = get_logger("agents.base")


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(
        self,
        model_name: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        """Initialize base agent with LLM configuration.

        Args:
            model_name: Claude model to use (defaults to settings.default_model)
            temperature: Generation temperature (defaults to settings.temperature)
            max_tokens: Maximum tokens to generate (defaults to settings.max_tokens)
        """
        self.model_name = model_name or settings.default_model
        self.temperature = temperature if temperature is not None else settings.temperature
        self.max_tokens = max_tokens or settings.max_tokens

        # Initialize LLM
        self.llm = self._initialize_llm()

        # Conversation history
        self.messages: list[BaseMessage] = []

        logger.info(
            f"Initialized {self.__class__.__name__} with model={self.model_name}, "
            f"temperature={self.temperature}"
        )

    def _initialize_llm(self) -> ChatAnthropic:
        """Initialize the Claude LLM."""
        if not settings.anthropic_api_key:
            raise LLMError(
                "ANTHROPIC_API_KEY not set. Please set it in your .env file or environment."
            )

        return ChatAnthropic(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=settings.anthropic_api_key,
        )

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent.

        Returns:
            System prompt string
        """
        pass

    def invoke(self, user_input: str, context: dict[str, Any] | None = None) -> str:
        """Invoke the agent with user input.

        Args:
            user_input: User's natural language input
            context: Optional context dictionary

        Returns:
            Agent's response as string
        """
        # Build messages
        messages = self._build_messages(user_input, context)

        try:
            # Invoke LLM
            response = self.llm.invoke(messages)
            response_text = response.content

            # Store in conversation history
            self.messages.append(HumanMessage(content=user_input))
            self.messages.append(response)

            logger.debug(f"Agent response: {response_text[:100]}...")

            return response_text

        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            raise LLMError(f"Failed to get response from LLM: {e}")

    def invoke_structured(
        self,
        user_input: str,
        output_schema: type[T],
        context: dict[str, Any] | None = None,
    ) -> T:
        """Invoke the agent and parse output into structured format.

        Args:
            user_input: User's natural language input
            output_schema: Pydantic model for structured output
            context: Optional context dictionary

        Returns:
            Parsed output matching the schema
        """
        # Build messages
        messages = self._build_messages(user_input, context)

        # Create LLM with structured output
        structured_llm = self.llm.with_structured_output(output_schema)

        try:
            # Invoke LLM
            response = structured_llm.invoke(messages)

            # Store in conversation history
            self.messages.append(HumanMessage(content=user_input))

            logger.debug(f"Structured response: {response}")

            return response

        except Exception as e:
            logger.error(f"Structured LLM invocation failed: {e}")
            raise LLMError(f"Failed to get structured response from LLM: {e}")

    def _build_messages(
        self, user_input: str, context: dict[str, Any] | None = None
    ) -> list[BaseMessage]:
        """Build message list for LLM invocation.

        Args:
            user_input: User input
            context: Optional context to include

        Returns:
            List of messages
        """
        messages = [SystemMessage(content=self.get_system_prompt())]

        # Add context if provided
        if context:
            context_str = self._format_context(context)
            messages.append(SystemMessage(content=f"Context:\n{context_str}"))

        # Add conversation history
        messages.extend(self.messages)

        # Add current user input
        messages.append(HumanMessage(content=user_input))

        return messages

    def _format_context(self, context: dict[str, Any]) -> str:
        """Format context dictionary for inclusion in prompt.

        Args:
            context: Context dictionary

        Returns:
            Formatted context string
        """
        lines = []
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.messages.clear()
        logger.debug("Conversation history cleared")

    def get_history(self) -> list[BaseMessage]:
        """Get conversation history.

        Returns:
            List of messages in conversation history
        """
        return self.messages.copy()
