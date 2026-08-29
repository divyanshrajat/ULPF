# ─── Stage 1: Build React frontend ──────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci --silent

COPY frontend/ ./
RUN npm run build

# Verify build succeeded
RUN test -d dist && test -f dist/index.html || (echo "ERROR: Frontend build failed — dist/index.html missing" && exit 1)

# ─── Stage 2: Build Python backend ───────────────────────────────────────────
FROM python:3.11-slim AS app

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend source
COPY backend/ .

# Copy compiled frontend into the backend image
# FastAPI serves it as static files — single origin, no CORS required
COPY --from=frontend-builder /frontend/dist /app/frontend/dist

# Vault directory
RUN mkdir -p /data/vault

ENV PYTHONPATH=/app
EXPOSE 8000
EXPOSE 5140/tcp
EXPOSE 5140/udp

# Run Alembic migrations then start the app
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
