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

COPY ./server .
COPY --from=frontend-builder /app/dist ./dist

RUN uv sync --frozen --no-cache

# --- Removed mv/sed/cat commands related to creating/populating .env file ---
# Backend code MUST be adapted to read DB_* variables via os.getenv()

# Kept original ENTRYPOINT/CMD - BUT likely needs changing for Render
ENTRYPOINT ["uv"]
CMD ["run", "fastapi", "run"]