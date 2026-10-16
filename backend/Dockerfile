# ==============================================================================
# RELIEFOS Lite — Production Backend Container
# Multi-stage security-hardened Python runtime for Disaster Management Operations
# ==============================================================================

FROM python:3.12-slim-bookworm AS builder

# Set build-time environment flags
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /install

# Install build dependencies for C-extensions (psycopg2, ortools, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install/deps -r requirements.txt

# Final Runtime Image
FROM python:3.12-slim-bookworm AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8013

WORKDIR /app

# Install minimal runtime libraries (libpq for PostgreSQL, curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install/deps /usr/local

# Create dedicated non-privileged user and data directory
RUN groupadd -r -g 1001 reliefos && \
    useradd -r -u 1001 -g reliefos -s /bin/bash -m reliefos && \
    mkdir -p /app/data /app/backups && \
    chown -R reliefos:reliefos /app

# Copy application source code
COPY --chown=reliefos:reliefos . /app

USER reliefos

# Container operational health check
HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8013/api/health || exit 1

EXPOSE 8013

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8013", "--workers", "2"]
