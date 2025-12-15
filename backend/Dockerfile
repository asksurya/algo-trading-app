# Production-ready Dockerfile for FastAPI backend

# --- Builder Stage ---
FROM python:3.12-slim as builder

WORKDIR /app

# Copy requirements file
COPY backend/requirements.txt ./

# Install dependencies to a virtual environment
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt && \
    NLTK_DATA=/opt/venv/nltk_data /opt/venv/bin/python -m textblob.download_corpora

# --- Runner Stage ---
FROM python:3.12-slim

WORKDIR /app

# Set non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="${PYTHONPATH}:/app"
ENV NLTK_DATA="/opt/venv/nltk_data"

# Copy application code
COPY backend/app ./app
COPY backend/gunicorn_conf.py .
COPY backend/alembic.ini .
COPY backend/migrations ./migrations
COPY src ./src

# Change ownership
RUN chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
