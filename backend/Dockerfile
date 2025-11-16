# Production-ready Dockerfile for FastAPI backend

# --- Builder Stage ---
FROM python:3.12-slim as builder

WORKDIR /app

# Set Poetry environment variables
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install Poetry
RUN pip install poetry

# Copy dependency definition files
COPY pyproject.toml poetry.lock ./

# Install dependencies (without dev dependencies)
RUN poetry install --no-dev

# --- Runner Stage ---
FROM python:3.12-slim

WORKDIR /app

# Set non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv ./.venv

# Activate virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY ./app ./app

# Expose port
EXPOSE 8000

# Run with Gunicorn
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "gunicorn_conf.py", "app.main:app"]
