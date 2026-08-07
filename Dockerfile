# ==========================================
# STAGE 1: Builder
# ==========================================
FROM python:3.14-rc-slim AS builder

WORKDIR /build

# Install build tools if needed for C-extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Build wheels for all dependencies
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt


# ==========================================
# STAGE 2: Runtime
# ==========================================
FROM python:3.14-rc-slim AS runtime

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy compiled wheels and install
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application code
COPY ./app ./app

# Set permissions
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Exec form CMD for FastAPI
CMD ["fastapi", "run", "app/main.py", "--port", "8000", "--host", "0.0.0.0"]
