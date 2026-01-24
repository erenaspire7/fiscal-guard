# Builder stage - install dependencies
FROM python:3.10-slim as builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Copy source code
COPY core ./core
COPY api ./api

# Install dependencies using uv (no cache to reduce size)
RUN uv sync --frozen --no-cache --package api

# Runtime stage - minimal final image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy only the necessary files from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/core /app/core
COPY --from=builder /app/api /app/api

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
