# STAGE 1: Builder stage
FROM python:3.12-slim AS builder

WORKDIR /app
COPY . /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Sync dependencies into virtual environment
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install -r pyproject.toml

# STAGE 2: Final runtime stage
FROM python:3.12-slim AS final

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source code
COPY app ./app

# Copy database migration and seed files
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic
COPY scripts ./scripts

# Create a non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Declare container port and healthcheck endpoint
EXPOSE 8000

# Container healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

# Exec-form CMD so SIGTERM signals pass through properly
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]