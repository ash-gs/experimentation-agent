# 🤖 Experimentation Agent 

An agentic AI system for automating the complete experimentation lifecycle, from hypothesis generation through experiment design, statistical analysis, and decision-making.

## 📌 Overview 

This project features a multi-agent system, partitioned into 4 specialized agents, each governing a distinct phase of experimentation: hypothesis, design, analysis, and decision-making. The system is exposed via a FastAPI REST API and orchestrated via n8n.

**Current Status:** Phases 1-4 Complete - All agents + API orchestration working

## ⭐ Features 

- **Hypothesis Generation**: AI generates testable hypotheses from business objectives
- **Experiment Design**: Automatic sample size calculation, power analysis, duration estimation, and variant configuration
- **Statistical Analysis**: t-tests, z-tests, chi-square, Mann-Whitney U, bootstrap testing with SRM detection
- **Decision Support**: Ship/no-ship/iterate recommendations with confidence scores and rationale
- **REST API**: FastAPI endpoints for each agent, ready for any frontend
- **Synthetic Data**: 3 built-in scenarios for testing and development

## ⚙️ Architecture 

### 🦾 Multi-Agent System 

| Agent | Purpose |
|-------|---------|
| **HypothesisAgent** | Takes business goals, generates testable hypotheses with metrics and expected effect sizes |
| **DesignAgent** | Creates experiment designs with sample sizes, duration, variants, guardrail metrics |
| **AnalysisAgent** | Runs statistical tests on experiment data, detects SRM, validates data quality |
| **DecisionAgent** | Makes ship/no-ship/iterate recommendations based on analysis results |

All agents use Claude via `langchain-anthropic` with structured output and YAML-based system prompts.

### 💻 Technology Stack 

- **LLM Integration**: `langchain-anthropic` + `langchain-core` (Claude Haiku / Opus)
- **API**: FastAPI + Uvicorn
- **Statistics**: scipy, statsmodels, pingouin
- **Data**: pandas + SQLAlchemy + SQLite + Pydantic
- **CLI**: Rich (hypothesis generation only)
- **Orchestration**: FastAPI REST API (n8n workflow example included)

## 📋 Project Structure

```
experimentation-agent/
├── src/testing_agent/
│   ├── agents/               # Agent implementations (base, hypothesis, design, analysis, decision)
│   ├── api/                  # FastAPI application
│   │   ├── app.py            # Main app setup with CORS
│   │   ├── dependencies.py   # Agent dependency injection
│   │   ├── schemas.py        # Request/response models
│   │   └── routes/           # Endpoint handlers
│   ├── config/
│   │   ├── settings.py       # Pydantic settings (env vars)
│   │   └── prompts/          # YAML prompt configs per agent
│   ├── data/
│   │   └── schemas.py        # Core data models (12+ Pydantic schemas)
│   ├── tools/
│   │   └── statistical/      # Power analysis, hypothesis testing, effect sizes, CIs, metrics
│   ├── synthetic/            # Synthetic data generation (3 scenarios)
│   ├── interface/            # Rich CLI
│   └── utils/                # Logging, exceptions
├── workflows/
│   └── n8n_examples/         # Example n8n workflow for API orchestration
├── tests/                    # Unit tests
├── scripts/                  # DB setup, synthetic data generation
└── data/                     # Local SQLite storage
```

## 🚩 Getting Started

### Prerequisites

- Python 3.11+
- Anthropic API key (get from https://console.anthropic.com/)

### Installation

1. **Clone and set up:**
   ```bash
   git clone <repo-url>
   cd experimentation-agent
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
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

### Run the API

```bash
uvicorn src.testing_agent.api.app:app --reload --port 8000
```

API docs available at http://localhost:8000/docs

## 🔗 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/hypothesis/generate` | Generate hypothesis from business goal |
| POST | `/api/v1/design/create` | Create experiment design from hypothesis |
| POST | `/api/v1/analysis/analyze` | Analyze experiment data |
| POST | `/api/v1/decision/make` | Make ship/no-ship recommendation |

### Example: Generate a Hypothesis

```bash
curl -X POST http://localhost:8000/api/v1/hypothesis/generate \
  -H "Content-Type: application/json" \
  -d '{"business_goal": "Increase checkout conversion rate by simplifying the payment form"}'
```

## 📈 Statistical Tools

The statistical toolkit includes:

- **Power Analysis**: Sample size calculation, power curves, minimum detectable effect
- **Hypothesis Testing**: Two-sample t-test, two-proportion z-test, chi-square, Mann-Whitney U, bootstrap
- **Effect Sizes**: Cohen's d/h, relative lift, odds ratio, risk ratio, NNT
- **Metrics**: Conversion rate aggregation, SRM detection, data quality validation
- **Confidence Intervals**: For proportions and means

## 📝 Synthetic Scenarios

Three built-in scenarios for testing:

| Scenario | Control | Treatment | Expected Result |
|----------|---------|-----------|-----------------|
| Button Color Test | 5.0% conversion | 5.5% conversion | Significant positive |
| Headline Test | 3.0% signup | 3.05% signup | No significance |
| Form Simplification | 60% completion | 55% completion | Significant negative |

## 🛠️ Configuration

Environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | (required) |
| `DEFAULT_MODEL` | Claude model for agents | claude-3-haiku-20240307 |
| `LOG_LEVEL` | Logging verbosity | INFO |
| `DATABASE_URL` | Database connection | sqlite:///data/experiments.db |
| `DEFAULT_POWER` | Statistical power | 0.8 |
| `DEFAULT_ALPHA` | Significance level | 0.05 |

## 📍 What's Complete

- Phase 1: Hypothesis Agent with Claude integration + CLI
- Phase 2: Statistical tools (power analysis, hypothesis testing, effect sizes, CIs)
- Phase 3: Design, Analysis, and Decision agents
- Phase 4: FastAPI orchestration with REST endpoints

## 🎯 Next Steps

- **Streamlit UI**: Web interface for running experiments end-to-end (password-protected, deployed on Streamlit Cloud)
- **Database persistence**: Wire up SQLAlchemy models to store experiment lifecycle
- **Integration tests**: End-to-end test coverage
- **Visualization**: Charts for power curves, effect size distributions, results

## 🔬 Testing

```bash
pytest                                    # Run all tests
pytest --cov=ab_testing_agent             # With coverage
pytest tests/unit/test_tools/             # Statistical tool tests only
```

## 🛡️ Code Quality

```bash
black src/ tests/                         # Format
ruff check src/ tests/                    # Lint
mypy src/                                 # Type check
```

## 📚 Resources

- [Anthropic Claude API](https://docs.anthropic.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Experimentation Best Practices](https://www.exp-platform.com/Documents/GuideControlledExperiments.pdf)

## 📄 License

MIT License