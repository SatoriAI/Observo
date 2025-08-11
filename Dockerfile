FROM python:3.13-slim

ARG APP_DIR=/source
WORKDIR ${APP_DIR}

ENV PATH=${APP_DIR}/.venv/bin:${PATH} \
		PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install uv (single static binary) and clean up
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh \
    && apt-get purge -y curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies with UV and no changes to the .lock file
COPY pyproject.toml uv.lock ${APP_DIR}/
RUN uv sync --frozen --no-dev

# Copy source code for Konfio
COPY observo/ ./observo/

# Probe /healtcheck every 30s, time out after 5s, start probing 10s after boot, retry 3x
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/healthcheck/ || exit 1
