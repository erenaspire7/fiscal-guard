"""FastAPI application for Fiscal Guard."""

import logging
import sys

from core.config import settings
from core.observability.tracing import setup_tracing
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from api.routers import (
    auth,
    budgets,
    chat,
    dashboard,
    decisions,
    goals,
    internal,
    users,
)

# Configure logging to output to stdout/stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Set specific loggers to DEBUG for detailed error tracking
logging.getLogger("core.ai.agents.conversation_swarm").setLevel(logging.DEBUG)
logging.getLogger("core.services.conversation").setLevel(logging.DEBUG)

# Initialise Strands OTLP tracing (no-op when OPIK_TRACING_ENABLED=false)
setup_tracing()

# Create FastAPI app
app = FastAPI(
    title="Fiscal Guard API",
    description="AI-powered financial decision assistant",
    version="0.1.0",
)

# Add session middleware for OAuth
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.jwt_secret_key,
)

# Add CORS middleware
# Allows requests from web UI and Chrome extension (chrome-extension://*)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # In production, specify allowed origins including chrome-extension://*
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(budgets.router)
app.include_router(goals.router)
app.include_router(decisions.router)
app.include_router(chat.router)

# Internal endpoints (only enabled when ALLOW_INTERNAL_ENDPOINTS=true)
if settings.allow_internal_endpoints:
    app.include_router(internal.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "Fiscal Guard API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
