# Use a specific Python slim image for the base
FROM python:3.12-slim-bookworm AS base

# --- Builder Stage ---
# Use the base image to build dependencies
FROM base AS builder

# Copy the uv binary from the official image
# Pinning to a specific version or SHA is recommended for reproducibility
# Using 'latest' here for simplicity, consider pinning e.g., ghcr.io/astral-sh/uv:0.4.9
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment variables for uv recommended in docs
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Set the working directory
WORKDIR /app

# Copy only the dependency definition files first to leverage Docker cache
COPY pyproject.toml uv.lock /app/

# Install dependencies using uv sync, leveraging build cache
# --no-install-project avoids installing the project itself in this layer
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Copy the rest of the application code
COPY . /app

# Install the project itself, leveraging build cache again
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# --- Final Stage ---
# Start from the clean base image
FROM base

# Set the working directory
WORKDIR /app

# Copy the virtual environment with installed dependencies from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Add the virtual environment's bin directory to the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy the application code from the builder stage
# This ensures only necessary files are in the final image
COPY --from=builder /app /app

# Copy the uv binary needed for the CMD
COPY --from=builder /bin/uv /bin/uv

# Copy the .env file (Consider security implications for production)
COPY .env /app/.env

# Command to run the application (based on your instructions)
# Loads variables from .env before running.
# NOTE: For production, consider injecting secrets via Docker secrets or runtime environment variables instead of copying .env
CMD ["sh", "-c", "set -a && source /app/.env && set +a && exec uv run mcp-zoho"]
