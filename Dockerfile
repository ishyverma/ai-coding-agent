# Simple single-stage Dockerfile for Railway
# Cache-bust: change this value to force a full rebuild
ARG CACHE_BUST=1
FROM python:3.11-slim

# Re-declare ARG after FROM to make it available in build stages
ARG CACHE_BUST
# This LABEL changes every build, invalidating all cached layers below
LABEL cache_bust=${CACHE_BUST}
RUN echo "Cache bust: ${CACHE_BUST}" > /tmp/.cache_bust && cat /tmp/.cache_bust

# Install system dependencies (needed for gitpython and SQLAlchemy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Go for running Go test commands
RUN curl -fsSL https://go.dev/dl/go1.23.4.linux-amd64.tar.gz | tar -C /usr/local -xz

# Install Node.js / npm for running npm test commands
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/usr/local/go/bin:${PATH}"

# Set working directory
WORKDIR /app

# Install Python dependencies first (Docker caches this layer)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY backend/ .

# Run as non-root user for security
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

# Railway sets PORT automatically
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
