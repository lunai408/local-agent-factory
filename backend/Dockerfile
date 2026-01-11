# Backend Dockerfile for Agno OS
FROM python:3.13-slim

WORKDIR /app

# Install curl for healthcheck and uv for package management
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files first (for better layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 7777

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:7777/v1/health || exit 1

# Run the application
CMD ["uv", "run", "uvicorn", "agentos:app", "--host", "0.0.0.0", "--port", "7777"]
