# Frontend pnpm build
FROM node:22-alpine AS frontend-builder

# Accept environment variables as build arguments
ARG GOOGLE_MAPS_API_KEY
ARG DB_NAME
ARG DB_USER
ARG DB_PASSWORD
ARG DB_HOST

# Set environment variables from ARG
ENV GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}
ENV DB_NAME=${DB_NAME}
ENV DB_USER=${DB_USER}
ENV DB_PASSWORD=${DB_PASSWORD}
ENV DB_HOST=${DB_HOST}

# Log the values of the ENV variables
RUN echo "GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}" && \
    echo "DB_NAME=${DB_NAME}" && \
    echo "DB_USER=${DB_USER}" && \
    echo "DB_PASSWORD=${DB_PASSWORD}" && \
    echo "DB_HOST=${DB_HOST}"

RUN corepack enable \
    && corepack prepare pnpm@latest --activate

WORKDIR /app

COPY client/package.json client/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY client/ ./

RUN mv src/config/index.ts.example src/config/index.ts

RUN sed -i "s/YOUR_GOOGLE_MAPS_API_KEY/${GOOGLE_MAPS_API_KEY}/" src/config/index.ts

RUN cat src/config/index.ts
RUN pnpm run build

# Python FastAPI server
FROM python:3.12-slim

# Accept environment variables as build arguments
ARG GOOGLE_MAPS_API_KEY
ARG DB_NAME
ARG DB_USER
ARG DB_PASSWORD
ARG DB_HOST

# Set environment variables from ARG
ENV GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}
ENV DB_NAME=${DB_NAME}
ENV DB_USER=${DB_USER}
ENV DB_PASSWORD=${DB_PASSWORD}
ENV DB_HOST=${DB_HOST}

RUN echo "GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}" && \
    echo "DB_NAME=${DB_NAME}" && \
    echo "DB_USER=${DB_USER}" && \
    echo "DB_PASSWORD=${DB_PASSWORD}" && \
    echo "DB_HOST=${DB_HOST}"

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
# Replace placeholders in .env with environment variables
RUN mv .env.example .env
RUN sed -i "s/YOUR_DB_NAME/${DB_NAME}/" .env
RUN sed -i "s/YOUR_DB_USER/${DB_USER}/" .env
RUN sed -i "s/YOUR_DB_PASSWORD/${DB_PASSWORD}/" .env
RUN sed -i "s/YOUR_DB_HOST/${DB_HOST}/" .env

RUN cat .env
ENV PYTHONPATH=/app

ENTRYPOINT ["uv"]
CMD ["run", "fastapi", "run"]