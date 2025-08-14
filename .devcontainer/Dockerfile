# Simple Python dev container with mise and uv
FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

USER root

# Install curl, Docker client, and Node.js
RUN apt-get update && apt-get install -y \
    curl \
    git \
    docker.io \
    && rm -rf /var/lib/apt/lists/* \
    && usermod -aG docker vscode 2>/dev/null || true

# Install Node.js (required for MCP dev server)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Create all necessary directories with proper permissions
RUN mkdir -p /home/vscode/.local/bin \
    /home/vscode/.cargo/bin \
    /home/vscode/.mise \
    /home/vscode/.cache/mise \
    /home/vscode/.cache/uv \
    /home/vscode/.vscode-server/extensions \
    && chown -R vscode:vscode /home/vscode \
    && chmod -R 755 /home/vscode/.cache

USER vscode

# Install mise and uv
RUN curl https://mise.run | sh && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    echo 'eval "$(/home/vscode/.local/bin/mise activate bash)"' >> /home/vscode/.bashrc && \
    echo 'export PATH="/home/vscode/.cargo/bin:$PATH"' >> /home/vscode/.bashrc

ENV PATH="/home/vscode/.local/bin:/home/vscode/.cargo/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    MISE_TRUSTED_CONFIG_PATHS=/workspace

WORKDIR /workspace

CMD ["sleep", "infinity"]