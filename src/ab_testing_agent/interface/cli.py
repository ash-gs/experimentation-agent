"""Command-line interface for AB Testing Agent."""

import sys
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ..agents.hypothesis import HypothesisAgent
from ..config.settings import settings
from ..utils.exceptions import ABTestingAgentError
from ..utils.logging import get_logger

console = Console()
logger = get_logger("cli")


def print_welcome():
    """Print welcome message."""
    welcome_text = """
# 🤖 AB Testing Agent

I can help you design, run, and analyze AB tests through natural language conversation.

**Phase 1**: Currently, I can help you generate testable hypotheses from your business goals.

Type your business goal or problem, and I'll create a hypothesis for testing.
Type 'quit' or 'exit' to end the session.
    """
    console.print(Panel(Markdown(welcome_text), title="Welcome", border_style="blue"))


def main():
    """Run the CLI interface."""
    # Check API key
    if not settings.anthropic_api_key:
        console.print(
            "[red]Error: ANTHROPIC_API_KEY not set.[/red]\n"
            "Please set it in your .env file or environment variables."
        )
        sys.exit(1)

    print_welcome()

    # Initialize agent
    try:
        agent = HypothesisAgent()
        console.print("[green]✓[/green] Hypothesis Agent initialized\n")
    except Exception as e:
        console.print(f"[red]Failed to initialize agent: {e}[/red]")
        sys.exit(1)

    # Main conversation loop
    while True:
        try:
            # Get user input
            user_input = console.input("\n[bold cyan]You:[/bold cyan] ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                console.print("\n[yellow]Goodbye! 👋[/yellow]")
                break

            # Show thinking indicator
            with console.status("[bold green]Thinking...", spinner="dots"):
                response = agent.generate_hypothesis_interactive(user_input)

            # Display response
            console.print(f"\n[bold magenta]🤖 Hypothesis Agent:[/bold magenta]")
            console.print(Markdown(response))

        except KeyboardInterrupt:
            console.print("\n\n[yellow]Interrupted. Goodbye! 👋[/yellow]")
            break
        except ABTestingAgentError as e:
            console.print(f"\n[red]Error: {e}[/red]")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            console.print(f"\n[red]Unexpected error: {e}[/red]")


if __name__ == "__main__":
    main()
