# ============================================================
# ACEest Fitness & Gym — Dockerfile
# Multi-stage build: lean, secure, production-ready
# ============================================================

# ---- Stage 1: Dependency Builder ----
FROM python:3.11-slim AS builder

WORKDIR /build

# Install dependencies into a local directory (no system pollution)
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ---- Stage 2: Final Runtime Image ----
FROM python:3.11-slim AS final

# Labels
LABEL maintainer="ACEest DevOps"
LABEL version="2.0.0"
LABEL description="ACEest Fitness & Gym - Flask Web Dashboard"

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    DB_NAME=/data/aceest_fitness.db

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY app.py .
COPY templates/ templates/

# Create persistent data directory for SQLite DB
RUN mkdir -p /data

# Create non-root user for security
RUN groupadd --system appgroup \
    && useradd --system --gid appgroup --no-create-home appuser \
    && chown -R appuser:appgroup /app /data

USER appuser

# Expose port
EXPOSE 5000

# Health check via /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Run with Gunicorn (production WSGI server)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "app:app"]
