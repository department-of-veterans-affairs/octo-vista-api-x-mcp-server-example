#!/usr/bin/env python3
"""Start mock server if not already running"""

import os
import subprocess
import sys
from pathlib import Path


def check_mock_server():
    """Check if mock server is running"""
    try:
        import urllib.error
        import urllib.request

        # Try both localhost and 127.0.0.1 (Windows sometimes has issues with localhost)
        urls = ["http://localhost:8888/health", "http://127.0.0.1:8888/health"]

        for url in urls:
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        return True
            except (urllib.error.URLError, urllib.error.HTTPError):
                continue

        return False
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

    # On Windows, Docker containers might take longer to be ready
    max_attempts = 30 if os.name == "nt" else 15
    wait_time = 3 if os.name == "nt" else 2

    print(
        f"⏳ Waiting for mock server to be ready (up to {max_attempts * wait_time} seconds)..."
    )

    # Extra initial delay for Windows
    if os.name == "nt":
        print("🪟 Windows detected - allowing extra startup time...")
        time.sleep(5)

    for attempt in range(max_attempts):
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

        print(f"⏳ Attempt {attempt + 1}/{max_attempts}: Waiting for mock server...")
        time.sleep(wait_time)

    print("\n❌ Mock server failed to start.")
    print("\n🔧 Troubleshooting tips:")
    print("1. Check if Docker Desktop is running")
    print("2. Check if port 8888 is already in use:")
    if os.name == "nt":
        print("   netstat -ano | findstr :8888")
    else:
        print("   lsof -i :8888")
    print("3. Check container status: docker ps -a")
    print("4. Check logs: docker logs vista-api-x-mock")
    print("5. Try accessing http://localhost:8888/health in your browser")
    if os.name == "nt":
        print("6. On Windows, try using 127.0.0.1 instead of localhost")
    sys.exit(1)


if __name__ == "__main__":
    main()
