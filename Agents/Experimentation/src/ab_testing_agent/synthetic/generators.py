"""Synthetic data generation for AB tests."""

import hashlib
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import numpy as np
from faker import Faker

from ..data.schemas import (
    DesignConfigSchema,
    Direction,
    ExperimentPhase,
    ExperimentStateSchema,
    ExperimentStatus,
    HypothesisSchema,
    RandomizationUnit,
    UserEventSchema,
    VariantSchema,
)
from .scenarios import ScenarioConfig, ScenarioType, get_scenario

fake = Faker()


class SyntheticDataGenerator:
    """Generate synthetic AB test data."""

    def __init__(self, seed: int | None = None):
        """Initialize generator with optional random seed."""
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)
            Faker.seed(seed)

    def generate_experiment_from_scenario(
        self, scenario_type: ScenarioType
    ) -> tuple[ExperimentStateSchema, list[UserEventSchema]]:
        """Generate a complete experiment from a predefined scenario."""
        scenario = get_scenario(scenario_type)
        return self.generate_experiment(scenario)

    def generate_experiment(
        self, scenario: ScenarioConfig
    ) -> tuple[ExperimentStateSchema, list[UserEventSchema]]:
        """Generate a complete experiment with synthetic data."""
        experiment_id = uuid4()

        # Create variants
        control_variant = VariantSchema(
            variant_id=uuid4(),
            name=scenario.control_name,
            description=scenario.control_description,
            allocation_percent=50.0,
            is_control=True,
        )

        treatment_variant = VariantSchema(
            variant_id=uuid4(),
            name=scenario.treatment_name,
            description=scenario.treatment_description,
            allocation_percent=50.0,
            is_control=False,
        )

        # Create hypothesis
        hypothesis = HypothesisSchema(
            description=scenario.hypothesis,
            metric=scenario.metric_name,
            expected_direction=scenario.expected_direction,
            expected_effect_size=abs(scenario.treatment_rate - scenario.control_rate),
            rationale=f"Based on hypothesis: {scenario.hypothesis}",
        )

        # Create design
        design = DesignConfigSchema(
            variants=[control_variant, treatment_variant],
            sample_size_per_variant=scenario.sample_size_per_variant,
            duration_days=scenario.duration_days,
            power=0.8,
            significance_level=0.05,
            minimum_detectable_effect=abs(scenario.treatment_rate - scenario.control_rate),
            randomization_unit=RandomizationUnit.USER,
            traffic_allocation=1.0,
        )

        # Create experiment state
        experiment = ExperimentStateSchema(
            experiment_id=experiment_id,
            name=scenario.name,
            phase=ExperimentPhase.COMPLETE,
            status=ExperimentStatus.COMPLETED,
            hypothesis=hypothesis,
            design=design,
        )

        # Generate events
        events = self._generate_events(
            experiment_id=experiment_id,
            control_variant=control_variant,
            treatment_variant=treatment_variant,
            scenario=scenario,
        )

        return experiment, events

    def _generate_events(
        self,
        experiment_id: UUID,
        control_variant: VariantSchema,
        treatment_variant: VariantSchema,
        scenario: ScenarioConfig,
    ) -> list[UserEventSchema]:
        """Generate user events for the experiment."""
        events: list[UserEventSchema] = []

        # Determine sample sizes (handle SRM if needed)
        if scenario.has_srm:
            # Intentionally unbalanced for SRM detection
            control_n = int(scenario.sample_size_per_variant * 0.45)
            treatment_n = int(scenario.sample_size_per_variant * 0.55)
        else:
            control_n = scenario.sample_size_per_variant
            treatment_n = scenario.sample_size_per_variant

        # Generate control events
        control_events = self._generate_variant_events(
            experiment_id=experiment_id,
            variant=control_variant,
            n_users=control_n,
            rate=scenario.control_rate,
            scenario=scenario,
            start_date=datetime.utcnow() - timedelta(days=scenario.duration_days),
            duration_days=scenario.duration_days,
        )
        events.extend(control_events)

        # Generate treatment events
        treatment_events = self._generate_variant_events(
            experiment_id=experiment_id,
            variant=treatment_variant,
            n_users=treatment_n,
            rate=scenario.treatment_rate,
            scenario=scenario,
            start_date=datetime.utcnow() - timedelta(days=scenario.duration_days),
            duration_days=scenario.duration_days,
        )
        events.extend(treatment_events)

        return events

    def _generate_variant_events(
        self,
        experiment_id: UUID,
        variant: VariantSchema,
        n_users: int,
        rate: float,
        scenario: ScenarioConfig,
        start_date: datetime,
        duration_days: int,
    ) -> list[UserEventSchema]:
        """Generate events for a single variant."""
        from ..data.schemas import MetricType

        events: list[UserEventSchema] = []

        # Generate users
        for i in range(n_users):
            user_id = self._generate_user_id(i, variant.variant_id)
            session_id = str(uuid4())

            # Generate exposure event
            event_timestamp = self._generate_timestamp(start_date, duration_days)

            exposure_event = UserEventSchema(
                user_id=user_id,
                session_id=session_id,
                experiment_id=experiment_id,
                variant_id=variant.variant_id,
                variant_name=variant.name,
                event_type="exposure",
                event_timestamp=event_timestamp,
            )
            events.append(exposure_event)

            # Determine if conversion/action happens based on rate
            if scenario.metric_type == MetricType.BINARY:
                # Binary metric (conversion, click, signup, etc.)
                converted = np.random.random() < rate

                if converted:
                    conversion_event = UserEventSchema(
                        user_id=user_id,
                        session_id=session_id,
                        experiment_id=experiment_id,
                        variant_id=variant.variant_id,
                        variant_name=variant.name,
                        event_type="conversion",
                        event_timestamp=event_timestamp + timedelta(seconds=np.random.randint(1, 300)),
                        metric_value=1.0,
                    )
                    events.append(conversion_event)

            elif scenario.metric_type == MetricType.CONTINUOUS:
                # Continuous metric (revenue, time on site, etc.)
                # Generate value from distribution with mean=rate and some variance
                if np.random.random() < 0.3:  # 30% of users have value
                    value = np.random.normal(rate, scenario.noise_std)
                    value = max(0, value)  # Ensure non-negative

                    value_event = UserEventSchema(
                        user_id=user_id,
                        session_id=session_id,
                        experiment_id=experiment_id,
                        variant_id=variant.variant_id,
                        variant_name=variant.name,
                        event_type="value",
                        event_timestamp=event_timestamp + timedelta(seconds=np.random.randint(1, 300)),
                        metric_value=value,
                    )
                    events.append(value_event)

        return events

    def _generate_user_id(self, index: int, variant_id: UUID) -> str:
        """Generate a deterministic hashed user ID."""
        raw_id = f"user_{index}_{variant_id}"
        return hashlib.md5(raw_id.encode()).hexdigest()[:16]

    def _generate_timestamp(self, start_date: datetime, duration_days: int) -> datetime:
        """Generate a random timestamp within the experiment duration."""
        seconds_in_duration = duration_days * 24 * 60 * 60
        random_seconds = np.random.randint(0, seconds_in_duration)
        return start_date + timedelta(seconds=random_seconds)


def generate_all_scenarios(
    seed: int | None = 42,
) -> list[tuple[ExperimentStateSchema, list[UserEventSchema]]]:
    """Generate all predefined scenarios."""
    generator = SyntheticDataGenerator(seed=seed)
    results = []

    for scenario_type in [
        ScenarioType.BUTTON_COLOR_POSITIVE,
        ScenarioType.HEADLINE_NULL,
        ScenarioType.FORM_NEGATIVE,
    ]:
        experiment, events = generator.generate_experiment_from_scenario(scenario_type)
        results.append((experiment, events))

    return results
