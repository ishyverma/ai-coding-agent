# Simple single-stage Dockerfile for Railway
FROM python:3.11-slim

# Install system dependencies (needed for gitpython and SQLAlchemy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies first (Docker caches this layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Run as non-root user for security
RUN useradd -m -u 1001 appuser
USER appuser

# Railway sets PORT automatically — we read it with $PORT
EXPOSE 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1