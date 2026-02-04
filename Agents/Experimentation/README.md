# AB Testing Agent 🤖

An agentic AI system for automating the complete AB testing experimentation lifecycle, from hypothesis generation through experiment design, execution, analysis, and decision-making.

## Overview

This project implements a multi-agent system using LangGraph and Claude that helps design, run, and analyze AB tests through natural language conversations.

**Current Status:** Phase 0 Complete - Foundation ✅

## Features (Planned)

- **Conversational Interface**: Describe your testing goals in natural language
- **Hypothesis Generation**: AI generates testable hypotheses from business objectives
- **Experiment Design**: Automatic sample size calculation, power analysis, and configuration
- **Statistical Analysis**: Rigorous statistical testing with proper interpretations
- **Decision Support**: Clear ship/no-ship recommendations with rationale
- **Synthetic Data**: Built-in scenarios for testing and development

## Architecture

### Multi-Agent System
- **Orchestrator Agent**: Routes requests and maintains conversation context
- **Hypothesis Agent**: Generates and refines experiment hypotheses
- **Design Agent**: Calculates sample sizes and experiment parameters
- **Analysis Agent**: Performs statistical tests and interprets results
- **Decision Agent**: Provides recommendations based on analysis

### Technology Stack
- **Agent Framework**: LangGraph + LangChain
- **LLM**: Anthropic Claude (3.5 Sonnet / Opus 4.5)
- **Statistics**: scipy, statsmodels, pingouin
- **Data**: pandas + SQLAlchemy + SQLite
- **Interface**: Rich CLI

## Project Structure

```
Agents/Experimentation/
├── src/ab_testing_agent/
│   ├── agents/              # Agent implementations
│   ├── workflows/           # LangGraph workflows
│   ├── tools/               # Statistical & data tools
│   │   ├── statistical/     # Power analysis, hypothesis testing
│   │   ├── data/            # Data loaders, validators
│   │   └── visualization/   # Plotting utilities
│   ├── data/                # Database models & schemas
│   ├── synthetic/           # Synthetic data generation
│   ├── config/              # Configuration & settings
│   └── interface/           # User interfaces
├── tests/                   # Test suite
├── scripts/                 # Utility scripts
└── data/                    # Local data storage
```

## Getting Started

### Prerequisites

- Python 3.11+
- Anthropic API key (get from https://console.anthropic.com/)

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd /Users/ashby/projects/Agents/Experimentation
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

5. **Initialize database:**
   ```bash
   python scripts/setup_db.py
   ```

6. **Generate synthetic data:**
   ```bash
   python scripts/generate_synthetic_data.py
   ```

### Verify Installation

Check that synthetic experiments were created:

```bash
sqlite3 data/experiments.db "SELECT name, phase, status FROM experiments;"
```

Expected output: 3 synthetic experiments (button color, headline test, form simplification)

## Phase 0 Complete ✅

### What's Working

- ✅ Project structure and dependencies
- ✅ Configuration system (Pydantic settings)
- ✅ Database models and schemas (SQLAlchemy + Pydantic)
- ✅ Synthetic data generation (3 scenarios)
- ✅ Data repository layer
- ✅ Logging infrastructure

### Synthetic Scenarios

1. **Button Color Test (Positive Effect)**
   - Control: 5.0% conversion
   - Treatment: 5.5% conversion
   - Expected: Statistically significant positive result

2. **Headline Test (Null Result)**
   - Control: 3.0% signup rate
   - Treatment: 3.05% signup rate
   - Expected: No statistical significance

3. **Form Simplification (Negative Effect)**
   - Control: 60% completion
   - Treatment: 55% completion
   - Expected: Significant negative result

## Development Roadmap

### Phase 1: Single Agent MVP (Next)
- Implement Hypothesis Agent with Claude integration
- Build simple CLI interface
- Add conversation memory

### Phase 2: Statistical Tools
- Power analysis (sample size calculation)
- Hypothesis testing (t-test, z-test, chi-square)
- Confidence intervals
- Basic visualizations

### Phase 3: Complete Agent Suite
- Design Agent
- Analysis Agent
- Decision Agent
- Integration tests

### Phase 4: LangGraph Orchestration
- Full workflow state machine
- End-to-end CLI
- Conversation checkpointing

### Future Phases
- Monitoring Agent (real-time tracking)
- Documentation Agent (automated reporting)
- Web UI (Streamlit)
- Data warehouse connectors

## Configuration

All configuration is managed through environment variables. See `.env.example` for available options:

- `ANTHROPIC_API_KEY`: Your Claude API key (required)
- `DEFAULT_MODEL`: Claude model for most agents
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `DATABASE_URL`: Database connection string
- `DEFAULT_POWER`: Statistical power for experiments (default: 0.8)
- `DEFAULT_ALPHA`: Significance level (default: 0.05)

## Data Models

### Key Schemas

- **ExperimentStateSchema**: Complete experiment through lifecycle
- **HypothesisSchema**: Testable hypothesis with metrics
- **DesignConfigSchema**: Experiment design parameters
- **AnalysisResultSchema**: Statistical test results
- **DecisionSchema**: Final recommendation with rationale

### Database Tables

- **experiments**: Experiment metadata and lifecycle state
- **variants**: Variant configurations (control, treatments)
- **user_events**: Individual user interactions and conversions
- **metric_definitions**: Metric catalog

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ab_testing_agent

# Run specific test file
pytest tests/unit/test_synthetic/test_generators.py
```

## Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Contributing

This is a personal experimentation project. Phase 0 establishes the foundation for the agentic AB testing system.

## License

MIT License - See LICENSE file for details

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [AB Testing Best Practices](https://www.exp-platform.com/Documents/GuideControlledExperiments.pdf)

## Contact

Questions or feedback? Open an issue in the repository.

---

**Status**: Phase 0 Complete - Foundation established with database, schemas, and synthetic data generation. Ready for Phase 1: First working agent with LLM integration.
