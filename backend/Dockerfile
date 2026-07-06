FROM python:3.11-slim-bookworm

# Install system dependencies (including uv)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency definitions
COPY pyproject.toml uv.lock ./

# Install dependencies (ignoring local package installs)
RUN uv sync --frozen --no-install-project --no-dev

# Copy source code
COPY . .

# Expose backend port
EXPOSE 8000

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV HOST=0.0.0.0
ENV PORT=8000

# Run uvicorn server, running migrations at startup
CMD uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
