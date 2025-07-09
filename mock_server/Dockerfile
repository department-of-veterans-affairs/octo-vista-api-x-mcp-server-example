# Use uv for fast Python package management
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim as builder

# Set working directory
WORKDIR /app

# Copy all files needed for build
COPY pyproject.toml README.md ./
COPY src ./src
COPY scripts ./scripts

# Install dependencies using uv
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN uv pip install .

# Final stage
FROM python:3.11-slim-bookworm

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 vistauser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=vistauser:vistauser . .

# Create keys directory (in case volume mount fails on Windows)
RUN mkdir -p /app/keys

# Set environment variables
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create logs directory
RUN mkdir -p logs && chown vistauser:vistauser logs

# Switch to non-root user
USER vistauser

# Expose ports
EXPOSE 8080 9990

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9990/health || exit 1

# Run the application
CMD ["python", "-m", "src.main"]