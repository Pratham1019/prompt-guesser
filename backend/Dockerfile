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

# Run migrations, auto-generate today's challenge, publish it, populate the buffer, and start the uvicorn server
CMD uv run alembic upgrade head && \
    uv run python manage.py generate-date --date today && \
    uv run python manage.py publish-today && \
    uv run python manage.py populate && \
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
