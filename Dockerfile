# ==============================================================================
# Stage 1: Build Frontend React Obsidian Dashboard
# ==============================================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /build

COPY dashboard/package*.json ./
RUN npm ci --prefer-offline --no-audit

COPY dashboard/ ./
RUN npm run build

# ==============================================================================
# Stage 2: Production Python Backend & Integrated Server
# ==============================================================================
FROM python:3.11-slim AS production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HOST=0.0.0.0 \
    PROMPTLENS_VAULT_BACKEND=sqlite \
    PROMPTLENS_VAULT_DB=/app/data/vault.db

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/
COPY rules/ ./rules/
COPY fixtures/ ./fixtures/

# Copy prebuilt frontend assets from stage 1
COPY --from=frontend-builder /build/dist ./dashboard/dist

# Create storage directory for persistent SQLite vault and metrics
RUN mkdir -p /app/data && chmod 777 /app/data
VOLUME ["/app/data"]

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "src.proxy.server:app", "--host", "0.0.0.0", "--port", "8000"]
