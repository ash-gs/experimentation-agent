"""Script to initialize the database."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from testing_agent.data.repositories import ExperimentRepository
from testing_agent.utils.logging import get_logger

logger = get_logger("setup_db")


def main():
    """Initialize database tables."""
    logger.info("Initializing database...")

    repo = ExperimentRepository()
    repo.create_tables()

    logger.info("Database tables created successfully!")
    logger.info(f"Database location: {repo.database_url}")


if __name__ == "__main__":
    main()
