# # Frontend pnpm build
# FROM node:18-alpine AS frontend-builder

# RUN corepack enable

# WORKDIR /app/client

# COPY client/package.json client/pnpm-lock.yaml ./
# RUN pnpm install --frozen-lockfile

# COPY client/ ./

# RUN mv src/config/index.ts.example src/config/index.ts

# RUN pnpm run build



# Python FastAPI server
FROM python:3.12-slim

WORKDIR /app

# Install GDAL & build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    gdal-bin \
    libgdal-dev && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.4.9 /uv /usr/local/bin/uv
RUN chmod +x /usr/local/bin/uv

COPY pyproject.toml ./

ENV GDAL_CONFIG=/usr/bin/gdal-config
RUN uv venv \
    && uv pip install .

COPY server ./server
COPY utils  ./utils
COPY client ./client
# COPY --from=frontend-builder /app/dist ./client

ENV PYTHONPATH=/app

ENTRYPOINT ["uv"]
CMD ["run", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]