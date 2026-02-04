"""Application configuration using Pydantic settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="AB Testing Agent", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    environment: Literal["development", "production"] = Field(
        default="development", description="Runtime environment"
    )

    # LLM Configuration
    anthropic_api_key: str = Field(default="", description="Anthropic API key for Claude")
    default_model: str = Field(
        default="claude-3-5-sonnet-20241022", description="Default Claude model"
    )
    complex_analysis_model: str = Field(
        default="claude-opus-4-5-20251101", description="Model for complex analysis tasks"
    )
    max_tokens: int = Field(default=4096, description="Maximum tokens for LLM responses")
    temperature: float = Field(default=0.7, description="LLM temperature for generation")

    # Database Configuration
    database_url: str = Field(
        default="sqlite:///data/experiments.db", description="Database connection URL"
    )
    echo_sql: bool = Field(default=False, description="Echo SQL statements (debug mode)")

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format",
    )
    log_file: str | None = Field(default=None, description="Optional log file path")

    # Statistical Configuration
    default_power: float = Field(default=0.8, description="Default statistical power (1 - β)")
    default_alpha: float = Field(
        default=0.05, description="Default significance level (α)"
    )
    default_confidence_level: float = Field(
        default=0.95, description="Default confidence level for intervals"
    )

    # Experiment Configuration
    min_sample_size: int = Field(
        default=1000, description="Minimum sample size per variant"
    )
    max_variants: int = Field(default=10, description="Maximum number of variants")
    default_traffic_allocation: float = Field(
        default=1.0, description="Default traffic allocation (0.0-1.0)"
    )

    # Paths
    @property
    def base_dir(self) -> Path:
        """Get base directory of the project."""
        return Path(__file__).parent.parent.parent.parent

    @property
    def data_dir(self) -> Path:
        """Get data directory path."""
        return self.base_dir / "data"

    @property
    def synthetic_data_dir(self) -> Path:
        """Get synthetic data directory path."""
        return self.data_dir / "synthetic"

    @property
    def exports_dir(self) -> Path:
        """Get exports directory path."""
        return self.data_dir / "exports"

    @property
    def prompts_dir(self) -> Path:
        """Get prompts directory path."""
        return Path(__file__).parent / "prompts"

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.synthetic_data_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Ensure directories exist on import
settings.ensure_directories()
