# Multi-stage production Dockerfile for 24/7 Cloud Deployment (Render, Railway, Fly.io, etc.)

# ---------------------------------------------------------------------------
# Stage 1: Build React Frontend
# ---------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 2: Python Runtime & Production Server
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runner

WORKDIR /app

# Install system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application and database
COPY day5-langgraph-agent/ ./day5-langgraph-agent/
COPY realestate-hub/ ./realestate-hub/

# Copy compiled frontend from builder
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose dynamic cloud port
ENV PORT=8000
ENV HOST=0.0.0.0
ENV PYTHONPATH="/app/day5-langgraph-agent:/app/realestate-hub/backend:${PYTHONPATH}"

EXPOSE 8000

WORKDIR /app/day5-langgraph-agent

CMD ["sh", "-c", "uvicorn vapi_server:app --host 0.0.0.0 --port ${PORT:-8000}"]
