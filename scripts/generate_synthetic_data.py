"""Script to generate synthetic experiment data."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from testing_agent.data.repositories import ExperimentRepository
from testing_agent.synthetic.generators import generate_all_scenarios
from testing_agent.utils.logging import get_logger

logger = get_logger("generate_synthetic_data")


def main():
    """Generate all synthetic scenarios and store in database."""
    logger.info("Generating synthetic experiment data...")

    # Initialize repository
    repo = ExperimentRepository()

    # Ensure tables exist
    repo.create_tables()

    # Generate all scenarios
    scenarios = generate_all_scenarios(seed=42)

    logger.info(f"Generated {len(scenarios)} scenarios")

    # Store each scenario
    for i, (experiment, events) in enumerate(scenarios, 1):
        logger.info(f"Storing scenario {i}/{len(scenarios)}: {experiment.name}")

        # Create experiment
        experiment_id = repo.create_experiment(experiment)
        logger.info(f"  Created experiment: {experiment_id}")

        # Add variants
        if experiment.design:
            repo.add_variants(experiment_id, experiment.design.variants)
            logger.info(f"  Added {len(experiment.design.variants)} variants")

        # Add events
        repo.add_events(events)
        logger.info(f"  Added {len(events)} events")

    logger.info("All synthetic data generated successfully!")
    logger.info(f"Database location: {repo.database_url}")

    # Verify
    experiments = repo.list_experiments()
    logger.info(f"\nTotal experiments in database: {len(experiments)}")
    for exp in experiments:
        logger.info(f"  - {exp.name} ({exp.phase.value}, {exp.status.value})")


if __name__ == "__main__":
    main()
