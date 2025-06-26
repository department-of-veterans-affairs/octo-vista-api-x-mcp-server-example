#!/usr/bin/env python3
"""Development server with mock - cross-platform"""

import os
import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_mock_server_status():
    """Check if mock server is running"""
    try:
        # Import check_mock_server here to avoid import errors
        from scripts.check_mock_server import check_mock_server

        return check_mock_server()
    except ImportError:
        # If httpx is not available, check using curl
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:8080/health"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except:
            return False


def start_mock_if_needed():
    """Start mock server if not running"""
    if not check_mock_server_status():
        print("🚀 Starting mock server...")

        # Check if Docker is running
        try:
            subprocess.run(["docker", "info"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Docker is not running. Please start Docker Desktop.")
            sys.exit(1)

        # Check if RSA keys exist, generate if needed
        keys_path = project_root / "mock_server" / "keys" / "private_key.pem"
        if not keys_path.exists():
            print("🔑 Generating RSA keys...")
            os.chdir(project_root / "mock_server")
            subprocess.run([sys.executable, "scripts/generate_rsa_keys.py"], check=True)

        # Start mock server
        os.chdir(project_root / "mock_server")
        subprocess.run(["docker-compose", "up", "-d"], check=True)

        # Wait for it to be ready
        if not check_mock_server_status():
            print("❌ Mock server failed to start. Check logs with: mise run logs")
            sys.exit(1)


def main():
    """Run MCP server with mock"""
    # Start mock server if needed
    start_mock_if_needed()

    # Run MCP server
    print("🏃 Starting MCP server...")
    os.chdir(project_root)
    subprocess.run(["uv", "run", "python", "server.py"])


if __name__ == "__main__":
    main()
