# Production-ready Dockerfile for FastAPI backend

# --- Builder Stage ---
FROM python:3.12-slim as builder

WORKDIR /app

# Copy requirements file
COPY requirements.txt ./

# Install dependencies to a virtual environment
RUN python -m venv /app/.venv && \
    /app/.venv/bin/pip install --upgrade pip && \
    /app/.venv/bin/pip install -r requirements.txt

# --- Runner Stage ---
FROM python:3.12-slim

WORKDIR /app

# Set non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv ./.venv

# Activate virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY ./app ./app
COPY gunicorn_conf.py .
COPY alembic.ini .
COPY migrations ./migrations

# Change ownership
RUN chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run with uvicorn using full path from virtual environment
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
