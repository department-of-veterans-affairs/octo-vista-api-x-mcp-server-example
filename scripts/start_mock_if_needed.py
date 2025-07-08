#!/usr/bin/env python3
"""Start mock server if not already running"""

import os
import subprocess
import sys
from pathlib import Path


def check_mock_server():
    """Check if mock server is running"""
    try:
        import urllib.request

        with urllib.request.urlopen(
            "http://localhost:8080/health", timeout=5
        ) as response:
            return response.status == 200
    except Exception:
        return False


def main():
    """Start mock server if needed"""
    if check_mock_server():
        print("✅ Mock server already running")
        return

    print("🚀 Starting mock server...")

    # Check if Docker is running
    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not running. Please start Docker Desktop.")
        sys.exit(1)

    project_root = Path(__file__).parent.parent

    # Check if RSA keys exist, generate if needed
    keys_path = project_root / "mock_server" / "keys" / "private_key.pem"
    if not keys_path.exists():
        print("🔑 Generating RSA keys...")
        # Use the Python from the virtual environment
        if os.name == "nt":  # Windows
            python_exe = str(project_root / ".venv" / "Scripts" / "python.exe")
        else:
            python_exe = str(project_root / ".venv" / "bin" / "python")

        subprocess.run(
            [
                python_exe,
                str(project_root / "mock_server" / "scripts" / "generate_rsa_keys.py"),
            ],
            cwd=project_root / "mock_server",
            check=True,
        )

    # Start mock server
    subprocess.run(
        ["docker-compose", "up", "-d"], cwd=project_root / "mock_server", check=True
    )

    # Wait for it to be ready
    import time

    for _ in range(10):
        if check_mock_server():
            print("✅ Mock server is ready!")

            # Initialize DynamoDB tables
            print("🗄️  Initializing DynamoDB tables...")
            try:
                subprocess.run(
                    [sys.executable, "scripts/init_mock_db.py"],
                    cwd=project_root,
                    check=True,
                )
            except subprocess.CalledProcessError:
                print("⚠️  Warning: Failed to initialize DynamoDB tables")
                print("   You may need to run: python scripts/init_mock_db.py")

            return
        time.sleep(2)

    print("❌ Mock server failed to start. Check logs with: mise run logs")
    sys.exit(1)


if __name__ == "__main__":
    main()
