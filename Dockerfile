# Accept GOOGLE_MAPS_API_KEY as a build argument
ARG GOOGLE_MAPS_API_KEY
ARG DB_NAME
ARG DB_USER
ARG DB_PASSWORD
ARG DB_HOST

# Frontend pnpm build
FROM node:22-alpine AS frontend-builder

RUN corepack enable \
    && corepack prepare pnpm@latest --activate

WORKDIR /app

COPY client/package.json client/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY client/ ./

RUN mv src/config/index.ts.example src/config/index.ts

RUN sed -i "s/YOUR_GOOGLE_MAPS_API_KEY/${GOOGLE_MAPS_API_KEY}/" src/config/index.ts
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
COPY --from=frontend-builder /app/dist ./app/dist

RUN uv sync --frozen --no-cache

ENV PYTHONPATH=/app

ENTRYPOINT ["uv"]
CMD ["run", "fastapi", "run"]