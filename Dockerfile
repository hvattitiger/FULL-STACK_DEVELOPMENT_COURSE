# ─────────────────────────────────────────────────────────────
# Stage 1 — Build React frontend
# ─────────────────────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Copy lock file first — lets Docker cache the npm ci layer
# as long as package.json and package-lock.json don't change
COPY frontend/package.json frontend/package-lock.json ./

# npm ci is faster than npm install — uses exact lock file versions
# --prefer-offline uses cache if available, --no-audit skips slow audit
RUN npm ci --prefer-offline --no-audit --no-fund

COPY frontend/ ./
RUN npm run build


# ─────────────────────────────────────────────────────────────
# Stage 2 — Python dependency builder
# ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS python-builder

WORKDIR /install

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ─────────────────────────────────────────────────────────────
# Stage 3 — Final runtime image
# ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Python packages
COPY --from=python-builder /install/lib /usr/local/lib
COPY --from=python-builder /install/bin /usr/local/bin

# FastAPI source
COPY app/ ./app/

# React built output (served as static files by FastAPI)
COPY --from=frontend-builder /frontend/dist ./frontend/

# Create data dir with correct permissions before switching user
RUN mkdir -p /app/data && chown -R appuser:appuser /app /app/data

ENV DATABASE_URL="sqlite:////app/data/task_tracker.db" \
    SECRET_KEY="change-me-in-production-use-openssl-rand-hex-32" \
    ALGORITHM="HS256" \
    ACCESS_TOKEN_EXPIRE_MINUTES="1440" \
    DEBUG="false"

VOLUME ["/app/data"]

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]