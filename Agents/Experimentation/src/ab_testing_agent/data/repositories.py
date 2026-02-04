"""Data access layer for experiments."""

from typing import Any
from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from ..config.settings import settings
from .models import Base, Experiment, UserEvent, Variant
from .schemas import ExperimentStateSchema, UserEventSchema, VariantSchema


class ExperimentRepository:
    """Repository for experiment data access."""

    def __init__(self, database_url: str | None = None):
        """Initialize repository with database connection."""
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url, echo=settings.echo_sql)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(self.engine)

    def drop_tables(self) -> None:
        """Drop all database tables (use with caution!)."""
        Base.metadata.drop_all(self.engine)

    def create_experiment(self, experiment: ExperimentStateSchema) -> str:
        """Create a new experiment."""
        with self.SessionLocal() as session:
            db_experiment = Experiment(
                experiment_id=str(experiment.experiment_id),
                name=experiment.name,
                phase=experiment.phase,
                status=experiment.status,
                created_at=experiment.created_at,
                updated_at=experiment.updated_at,
                created_by=experiment.created_by,
            )

            # Add hypothesis if present
            if experiment.hypothesis:
                db_experiment.hypothesis_description = experiment.hypothesis.description
                db_experiment.hypothesis_metric = experiment.hypothesis.metric
                db_experiment.hypothesis_direction = experiment.hypothesis.expected_direction
                db_experiment.hypothesis_effect_size = experiment.hypothesis.expected_effect_size
                db_experiment.hypothesis_rationale = experiment.hypothesis.rationale

            # Add design if present
            if experiment.design:
                db_experiment.sample_size_per_variant = experiment.design.sample_size_per_variant
                db_experiment.duration_days = experiment.design.duration_days
                db_experiment.power = experiment.design.power
                db_experiment.significance_level = experiment.design.significance_level
                db_experiment.minimum_detectable_effect = experiment.design.minimum_detectable_effect
                db_experiment.randomization_unit = experiment.design.randomization_unit
                db_experiment.traffic_allocation = experiment.design.traffic_allocation

                # Store design config as JSON
                db_experiment.design_config = experiment.design.model_dump(mode="json")

            # Add decision if present
            if experiment.decision:
                db_experiment.decision_recommendation = experiment.decision.recommendation
                db_experiment.decision_rationale = experiment.decision.rationale
                db_experiment.decision_confidence = experiment.decision.confidence

            # Store conversation history
            db_experiment.conversation_history = experiment.conversation_history

            session.add(db_experiment)
            session.commit()
            return db_experiment.experiment_id

    def get_experiment(self, experiment_id: UUID | str) -> ExperimentStateSchema | None:
        """Get an experiment by ID."""
        with self.SessionLocal() as session:
            stmt = select(Experiment).where(Experiment.experiment_id == str(experiment_id))
            db_experiment = session.scalar(stmt)

            if not db_experiment:
                return None

            return self._experiment_to_schema(db_experiment)

    def update_experiment(self, experiment: ExperimentStateSchema) -> None:
        """Update an existing experiment."""
        with self.SessionLocal() as session:
            stmt = select(Experiment).where(
                Experiment.experiment_id == str(experiment.experiment_id)
            )
            db_experiment = session.scalar(stmt)

            if not db_experiment:
                raise ValueError(f"Experiment {experiment.experiment_id} not found")

            # Update fields
            db_experiment.name = experiment.name
            db_experiment.phase = experiment.phase
            db_experiment.status = experiment.status
            db_experiment.updated_at = experiment.updated_at

            # Update hypothesis
            if experiment.hypothesis:
                db_experiment.hypothesis_description = experiment.hypothesis.description
                db_experiment.hypothesis_metric = experiment.hypothesis.metric
                db_experiment.hypothesis_direction = experiment.hypothesis.expected_direction
                db_experiment.hypothesis_effect_size = experiment.hypothesis.expected_effect_size
                db_experiment.hypothesis_rationale = experiment.hypothesis.rationale

            # Update design
            if experiment.design:
                db_experiment.sample_size_per_variant = experiment.design.sample_size_per_variant
                db_experiment.duration_days = experiment.design.duration_days
                db_experiment.power = experiment.design.power
                db_experiment.significance_level = experiment.design.significance_level
                db_experiment.minimum_detectable_effect = experiment.design.minimum_detectable_effect
                db_experiment.randomization_unit = experiment.design.randomization_unit
                db_experiment.traffic_allocation = experiment.design.traffic_allocation
                db_experiment.design_config = experiment.design.model_dump(mode="json")

            # Update decision
            if experiment.decision:
                db_experiment.decision_recommendation = experiment.decision.recommendation
                db_experiment.decision_rationale = experiment.decision.rationale
                db_experiment.decision_confidence = experiment.decision.confidence

            db_experiment.conversation_history = experiment.conversation_history

            session.commit()

    def add_variants(self, experiment_id: UUID | str, variants: list[VariantSchema]) -> None:
        """Add variants to an experiment."""
        with self.SessionLocal() as session:
            for variant in variants:
                db_variant = Variant(
                    variant_id=str(variant.variant_id),
                    experiment_id=str(experiment_id),
                    name=variant.name,
                    description=variant.description,
                    allocation_percent=variant.allocation_percent,
                    is_control=variant.is_control,
                )
                session.add(db_variant)
            session.commit()

    def add_events(self, events: list[UserEventSchema]) -> None:
        """Add user events."""
        with self.SessionLocal() as session:
            for event in events:
                db_event = UserEvent(
                    event_id=str(event.event_id),
                    user_id=event.user_id,
                    session_id=event.session_id,
                    experiment_id=str(event.experiment_id),
                    variant_id=str(event.variant_id),
                    variant_name=event.variant_name,
                    event_type=event.event_type,
                    event_timestamp=event.event_timestamp,
                    metric_value=event.metric_value,
                    properties=event.properties,
                )
                session.add(db_event)
            session.commit()

    def get_experiment_events(self, experiment_id: UUID | str) -> list[UserEventSchema]:
        """Get all events for an experiment."""
        with self.SessionLocal() as session:
            stmt = select(UserEvent).where(UserEvent.experiment_id == str(experiment_id))
            db_events = session.scalars(stmt).all()

            return [
                UserEventSchema(
                    event_id=UUID(event.event_id),
                    user_id=event.user_id,
                    session_id=event.session_id,
                    experiment_id=UUID(event.experiment_id),
                    variant_id=UUID(event.variant_id),
                    variant_name=event.variant_name,
                    event_type=event.event_type,
                    event_timestamp=event.event_timestamp,
                    metric_value=event.metric_value,
                    properties=event.properties or {},
                )
                for event in db_events
            ]

    def list_experiments(self, limit: int = 100) -> list[ExperimentStateSchema]:
        """List all experiments."""
        with self.SessionLocal() as session:
            stmt = select(Experiment).limit(limit).order_by(Experiment.created_at.desc())
            db_experiments = session.scalars(stmt).all()

            return [self._experiment_to_schema(exp) for exp in db_experiments]

    def _experiment_to_schema(self, db_experiment: Experiment) -> ExperimentStateSchema:
        """Convert database model to schema."""
        from .schemas import (
            DesignConfigSchema,
            DecisionSchema,
            HypothesisSchema,
        )

        # Build hypothesis
        hypothesis = None
        if db_experiment.hypothesis_description:
            hypothesis = HypothesisSchema(
                description=db_experiment.hypothesis_description,
                metric=db_experiment.hypothesis_metric or "",
                expected_direction=db_experiment.hypothesis_direction or Direction.INCREASE,
                expected_effect_size=db_experiment.hypothesis_effect_size or 0.0,
                rationale=db_experiment.hypothesis_rationale,
            )

        # Build design
        design = None
        if db_experiment.design_config:
            design = DesignConfigSchema(**db_experiment.design_config)

        # Build decision
        decision = None
        if db_experiment.decision_recommendation:
            decision = DecisionSchema(
                recommendation=db_experiment.decision_recommendation,
                rationale=db_experiment.decision_rationale or "",
                confidence=db_experiment.decision_confidence or 0.5,
            )

        return ExperimentStateSchema(
            experiment_id=UUID(db_experiment.experiment_id),
            name=db_experiment.name,
            phase=db_experiment.phase,
            status=db_experiment.status,
            hypothesis=hypothesis,
            design=design,
            decision=decision,
            conversation_history=db_experiment.conversation_history or [],
            created_at=db_experiment.created_at,
            updated_at=db_experiment.updated_at,
            created_by=db_experiment.created_by,
        )
