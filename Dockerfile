# Multi-stage production Dockerfile for 24/7 Cloud Deployment on Render.com

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

ENV HOST=0.0.0.0
ENV PYTHONPATH="/app/day5-langgraph-agent:/app/realestate-hub/backend:${PYTHONPATH}"

WORKDIR /app/day5-langgraph-agent

# Render automatically sets $PORT (typically 10000)
CMD ["sh", "-c", "uvicorn vapi_server:app --host 0.0.0.0 --port ${PORT:-10000}"]
