#!/bin/bash
set -e

echo "🚀 Setting up development environment..."

# Test Docker/Podman connectivity
echo "🔍 Checking Docker connectivity..."
if docker version &>/dev/null; then
    echo "✅ Docker client connected to Podman API"
else
    echo "⚠️  Docker not available. Ensure Podman API is running on Windows host:"
    echo "   Run: .\\scripts\\mock-server.ps1 start"
fi

# Verify Node.js is installed
echo "🔍 Checking Node.js..."
if node --version &>/dev/null; then
    echo "✅ Node.js $(node --version) installed"
else
    echo "⚠️  Node.js not found - MCP dev server will not work"
fi

# Fix Git to handle Windows CRLF line endings
echo "🔧 Configuring Git for Windows line endings..."
git config --global core.autocrlf input
git config --global core.filemode false

# Ensure cache directories have correct permissions
echo "📁 Setting up cache directories..."
mkdir -p ~/.cache/mise ~/.cache/uv ~/.mise
chmod -R 755 ~/.cache ~/.mise

# Trust mise config and install tools
cd /workspace
echo "🔧 Configuring mise..."
export MISE_TRUSTED_CONFIG_PATHS=/workspace
export MISE_EXPERIMENTAL=0
mise trust --all 2>/dev/null || true

echo "📦 Installing tools via mise..."
mise install || true

# Install Python dependencies
if [ -f pyproject.toml ]; then
    echo "🐍 Setting up Python environment..."
    uv venv .venv --python 3.12 || true
    uv pip install -e . || true
fi

echo ""
echo "✅ Setup complete! Available commands:"
echo "  mise run dev-with-mock     - Start with mock server"
echo "  mise run test              - Run tests"
echo "  mise run lint              - Run linting"
echo ""
echo "Note: Mock server runs on Windows host, not in container"
echo "  On host: .\\scripts\\mock-server.ps1 start"