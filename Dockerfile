# Frontend pnpm build
FROM node:22-alpine AS frontend-builder


RUN corepack enable \
    && corepack prepare pnpm@latest --activate

WORKDIR /app

COPY client/package.json client/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY client/ ./

ENV VITE_API_BASE_URL=""

RUN pnpm run build

# RAG Builder
FROM python:3.12-slim AS rag-builder

# Install uv, just like in the final stage
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app/server

# Copy only the necessary files to install dependencies
COPY ./server/pyproject.toml ./server/uv.lock* ./
RUN uv sync --frozen --no-cache

# Copy the knowledge base source and the script to build the index
COPY ./server/knowledge.jsonl ./
COPY ./server/create_vector_store.py ./

# This is the crucial step: Run the script to generate the faiss_index.
# We use Docker secrets to securely pass the API key during the build process.
# This key will NOT be stored in the final image layer.
RUN --mount=type=secret,id=openai_api_key \
    OPENAI_API_KEY=$(cat /run/secrets/openai_api_key) python create_vector_store.py

# After this stage, a /app/server/faiss_index directory will be created and ready.

# Python FastAPI server
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV PYTHONPATH=/app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    gdal-bin \
    libgdal-dev && \
    rm -rf /var/lib/apt/lists/*

ENV GDAL_CONFIG=/usr/bin/gdal-config

# Preserve package structure so imports like `from server.config...` work
COPY ./server /app/server
# Place built frontend inside the server package so relative 'dist' path works
COPY --from=frontend-builder /app/dist /app/server/dist

# Install Python dependencies (pyproject.toml is inside /app/server)
WORKDIR /app/server
RUN uv sync --frozen --no-cache
# Keep runtime working directory at project (server) root for uv to find pyproject

# --- Removed mv/sed/cat commands related to creating/populating .env file ---
# Backend code MUST be adapted to read DB_* variables via os.getenv()
ENV APP_ENV=production
ENV CORS_ORIGINS=*

# Kept original ENTRYPOINT/CMD - BUT likely needs changing for Render
ENTRYPOINT ["uv"]
# Run using uvicorn directly (fastapi CLI not installed by default)
CMD ["run", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]