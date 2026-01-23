"""FastAPI application for Fiscal Guard."""

from core.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from api.routers import auth, budgets, dashboard, decisions, goals, users

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
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
