# Stage 1: Build stage
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

# Copy UV binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Disable development dependencies
ENV UV_NO_DEV=1

# Install dependencies in a virtual environment
RUN uv sync --locked --no-install-project

# Copy application code
COPY src/ .

# Install the project itself
RUN uv sync --locked --no-dev

# Stage 2: Runtime stage
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Copy only the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --from=builder /app /app

# Create non-root user
RUN useradd --create-home --no-log-init appuser && \
    chown -R appuser:appuser /app

# Set PATH to use virtual environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER appuser

# Expose the default FastAPI port
EXPOSE 8080

# Start the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
