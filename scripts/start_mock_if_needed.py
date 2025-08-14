#!/usr/bin/env python3
"""Start mock server if not already running"""

import os
import subprocess
import sys
import time
from pathlib import Path


def is_in_container():
    """Check if running inside a container"""
    return (
        os.path.exists("/.dockerenv") or os.environ.get("REMOTE_CONTAINERS") == "true"
    )


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

    # Check if we're in a container
    in_container = is_in_container()

    if in_container:
        # In devcontainer, check if mock is accessible on host
        print("📦 Running in devcontainer - checking mock server on host...")

        # Try multiple addresses where mock might be running
        mock_urls = [
            "http://host.docker.internal:8888/health",  # Docker Desktop / Podman
            "http://localhost:8888/health",  # Direct localhost
            "http://127.0.0.1:8888/health",  # Explicit IP
        ]

        for url in mock_urls:
            try:
                import urllib.request

                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=2) as response:
                    if response.status == 200:
                        print(
                            f"✅ Mock server is accessible at {url.replace('/health', '')}"
                        )
                        return
            except Exception:
                continue

        print("⚠️  Mock server not accessible from devcontainer")
        print("   On Windows host, run: .\\scripts\\mock-server.ps1 status")
        print("   If mock server is not running: .\\scripts\\mock-server.ps1 start")
        print("")
        print("   Continuing anyway - mock server may not be needed for all operations")
        return  # Don't exit, just warn

    print("🚀 Starting mock server...")

    # Check if Docker is running (works with both Docker and Podman via socket)
    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not running. Please start Docker Desktop or Podman.")
        print("   If using Podman on Windows, run: .\\scripts\\mock-server.ps1 start")
        sys.exit(1)

    project_root = Path(__file__).parent.parent

    # Check if RSA keys exist, generate if needed
    keys_path = project_root / "mock_server" / "keys" / "private_key.pem"
    if not keys_path.exists():
        print("🔑 Generating RSA keys...")

        # Check if we're in a container
        in_container = (
            os.path.exists("/.dockerenv")
            or os.environ.get("REMOTE_CONTAINERS") == "true"
        )

        if in_container:
            # In container, use the /tmp venv or system python
            venv_path = Path("/tmp/workspace-venv")
            if venv_path.exists():
                python_exe = str(venv_path / "bin" / "python")
            else:
                python_exe = sys.executable

            # Install cryptography first
            result = subprocess.run(
                ["uv", "pip", "install", "--python", str(venv_path), "cryptography"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"⚠️  Warning: Failed to install cryptography: {result.stderr}")
                print("   RSA key generation may fail")
        elif os.name == "nt":  # Windows
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
    print("🚀 Starting containers...")

    # Check if we're in a container with Podman
    in_container = (
        os.path.exists("/.dockerenv") or os.environ.get("REMOTE_CONTAINERS") == "true"
    )

    if in_container and os.environ.get("DOCKER_HOST", "").startswith("tcp://"):
        # In devcontainer with Podman - need special handling
        print("📦 Using Podman compatibility mode...")

        # Check if containers are already running
        existing_containers = (
            subprocess.run(
                ["docker", "ps", "-a", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
            )
            .stdout.strip()
            .split("\n")
        )

        # Remove any existing stopped containers
        for container in [
            "vista-localstack",
            "vista-api-x-mock",
            "vista-dynamodb-admin",
        ]:
            if container in existing_containers:
                print(f"🧹 Removing existing {container} container...")
                subprocess.run(["docker", "rm", "-f", container], capture_output=True)

        # Pull images individually (more reliable with Podman)
        print("📥 Pulling required images (this may take a while)...")
        images_to_pull = [
            ("localstack/localstack:3.0.2", "LocalStack"),
            ("aaronshaf/dynamodb-admin:latest", "DynamoDB Admin"),
        ]

        for image, name in images_to_pull:
            print(f"   Pulling {name}...")
            for attempt in range(3):  # Retry up to 3 times
                result = subprocess.run(
                    ["docker", "pull", image], capture_output=True, text=True
                )
                if result.returncode == 0:
                    print(f"   ✅ {name} pulled successfully")
                    break
                else:
                    if (
                        "input/output error" in result.stderr
                        or "socket hang up" in result.stderr
                    ):
                        print(f"   ⚠️  Retry {attempt + 1}/3 for {name}...")
                        time.sleep(2)
                    else:
                        print(f"   ❌ Failed to pull {name}: {result.stderr}")
                        break

        # Build vista-mock image
        print("🔨 Building vista-mock image...")
        result = subprocess.run(
            ["docker", "build", "-t", "vista-mock:latest", "-f", "Dockerfile", "."],
            cwd=project_root / "mock_server",
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("   ✅ vista-mock image built successfully")
        else:
            print(f"   ⚠️  Could not build vista-mock: {result.stderr[:200]}")

        # Start containers individually (more reliable with Podman)
        print("🚀 Starting containers...")

        # Start localstack
        print("   Starting LocalStack...")
        result = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                "vista-localstack",
                "-p",
                "4566:4566",
                "-e",
                "SERVICES=dynamodb",
                "-e",
                "DEBUG=1",
                "-e",
                "DATA_DIR=/var/lib/localstack/data",
                "localstack/localstack:3.0.2",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("   ✅ LocalStack started")
        else:
            print(f"   ⚠️  LocalStack failed: {result.stderr[:200]}")

        # Wait for localstack to be ready
        time.sleep(5)

        # Start vista-mock
        print("   Starting Vista Mock Server...")
        result = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                "vista-api-x-mock",
                "-p",
                "8888:8080",
                "-p",
                "9990:9990",
                "-e",
                "AWS_ENDPOINT_URL=http://host.docker.internal:4566",
                "-e",
                "AWS_ACCESS_KEY_ID=test",
                "-e",
                "AWS_SECRET_ACCESS_KEY=test",
                "-e",
                "AWS_DEFAULT_REGION=us-east-1",
                "-v",
                f"{project_root}/mock_server/keys:/app/keys:ro",
                "vista-mock:latest",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("   ✅ Vista Mock Server started")
        else:
            print(f"   ⚠️  Vista Mock failed: {result.stderr[:200]}")

        print("✅ Mock server setup complete")
    else:
        # Normal docker-compose (Mac or Linux with Docker)
        subprocess.run(
            ["docker-compose", "up", "-d"], cwd=project_root / "mock_server", check=True
        )

    # Wait for it to be ready

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
