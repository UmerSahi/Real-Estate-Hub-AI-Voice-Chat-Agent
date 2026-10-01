# Multi-stage production Dockerfile for 24/7 Cloud Deployment on Render.com

# ---------------------------------------------------------------------------
# Stage 1: Build React Frontend
# ---------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Install dependencies with devDependencies included (required for vite)
COPY frontend/package*.json ./
RUN npm ci --include=dev

# Copy frontend source code and build production assets
COPY frontend/ ./
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 2: Python Runtime & Production Server
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required for LightGBM, ChromaDB, SHAP, and PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    gcc \
    g++ \
    libpq-dev \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools, and wheel for clean C-extension compilation on Python 3.12
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application, real estate hub, and machine learning models
COPY day5-langgraph-agent/ ./day5-langgraph-agent/
COPY realestate-hub/ ./realestate-hub/
# Use JSON array syntax for paths containing whitespace
COPY ["Week 8/", "./Week 8/"]

# Create symlink so both 'Week 8' and 'week8' paths resolve identically
RUN ln -s "/app/Week 8" "/app/week8" 2>/dev/null || true

# Copy compiled frontend from builder into both root and agent directories for reliable static serving
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist
COPY --from=frontend-builder /app/frontend/dist /app/day5-langgraph-agent/dist

ENV HOST=0.0.0.0
ENV PYTHONPATH="/app/day5-langgraph-agent:/app/realestate-hub/backend:/app/Week 8/Day 4:/app/week8/Day 4"

WORKDIR /app/day5-langgraph-agent

# Render automatically sets $PORT (typically 10000)
CMD ["sh", "-c", "uvicorn vapi_server:app --host 0.0.0.0 --port ${PORT:-10000}"]
