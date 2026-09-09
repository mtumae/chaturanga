FROM python:3.11-slim-bookworm

# 1. Grab the official standalone uv binary from Astral
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 2. Install Stockfish and curl via apt
RUN apt-get update && apt-get install -y --no-install-recommends \
    stockfish \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. Optimize uv settings for Docker:
# - Compile bytecode during install so app boots faster
# - Copy mode instead of symlinks
# - Disable dev dependencies
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    STOCKFISH_PATH=/usr/games/stockfish \
    PATH="/app/.venv/bin:$PATH"

# 4. Copy dependency specifications first to leverage Docker layer caching
COPY pyproject.toml uv.lock ./

# 5. Install dependencies into /app/.venv without installing root app yet
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# 6. Copy source code
COPY . .

# 7. Sync the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

EXPOSE 8000

# 8. Run uvicorn directly from the virtualenv (already on PATH)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
