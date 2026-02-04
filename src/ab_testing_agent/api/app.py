"""Main FastAPI application setup."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config.settings import settings

# Create FastAPI app
app = FastAPI(
    title="AB Testing Agent API",
    description="API for orchestrating AB testing experiments with AI agents",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for n8n
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AB Testing Agent API",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }


# Import and include routers
from .routes import analysis, decision, design, health, hypothesis  # noqa: E402

app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(hypothesis.router, prefix="/api/v1/hypothesis", tags=["Hypothesis"])
app.include_router(design.router, prefix="/api/v1/design", tags=["Design"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(decision.router, prefix="/api/v1/decision", tags=["Decision"])
