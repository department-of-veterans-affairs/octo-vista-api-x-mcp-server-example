#!/usr/bin/env python3
"""Start Local Development Cache Infrastructure

This script starts Redis and monitoring tools for local development.
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, check=True, capture_output=False):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd, shell=True, check=check, capture_output=capture_output, text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            raise
        return e


def check_docker():
    """Check if Docker is running."""
    print("Checking Docker status...")
    result = run_command("docker info", check=False, capture_output=True)
    if result.returncode != 0:
        print("Docker is not running. Please start Docker first.")
        return False
    print("Docker is running")
    return True


def check_docker_compose():
    """Check if docker-compose is available."""
    result = run_command("docker-compose --version", check=False, capture_output=True)
    if result.returncode != 0:
        print("docker-compose is not available. Please install it first.")
        return False
    print("docker-compose is available")
    return True


def is_redis_running():
    """Check if Redis container is already running."""
    result = run_command(
        "docker ps --format '{{.Names}}' | grep -q vista-local-redis", check=False
    )
    return result.returncode == 0


def wait_for_redis_healthy(timeout=30):
    """Wait for Redis container to be healthy."""
    print("Waiting for Redis to be ready...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        result = run_command(
            "docker ps --format '{{.Names}} {{.Status}}' | grep vista-local-redis | grep -q healthy",
            check=False,
        )
        if result.returncode == 0:
            print("Redis is ready!")
            return True

        time.sleep(1)

    print("Redis failed to start within 30 seconds")
    return False


def start_redis():
    """Start Redis container."""
    print("Starting Redis container...")
    project_root = Path(__file__).parent.parent
    compose_file = project_root / "docker-compose.local.yml"

    result = run_command(f"docker-compose -f {compose_file} up -d redis-local")
    if result.returncode != 0:
        print("Failed to start Redis container")
        return False

    return wait_for_redis_healthy()


def start_monitoring_tools():
    """Start optional monitoring tools."""
    print("Starting monitoring tools...")
    project_root = Path(__file__).parent.parent
    compose_file = project_root / "docker-compose.local.yml"

    result = run_command(
        f"docker-compose -f {compose_file} up -d redis-commander redis-insight"
    )
    if result.returncode == 0:
        print("Monitoring tools started:")
        print("   - Redis Commander: http://localhost:8081")
        print("   - Redis Insight: http://localhost:8001")
    else:
        print("Failed to start monitoring tools")


def main():
    """Main function to start local cache infrastructure."""
    print("Starting Local Development Cache Infrastructure")
    print("=" * 50)

    # Check prerequisites
    if not check_docker():
        sys.exit(1)

    if not check_docker_compose():
        sys.exit(1)

    # Check if Redis is already running
    if is_redis_running():
        print("Redis is already running")
    else:
        if not start_redis():
            sys.exit(1)

    # Start optional monitoring tools
    if len(sys.argv) > 1 and sys.argv[1] == "--with-monitoring":
        start_monitoring_tools()

    # Print success message and instructions
    print("")
    print("Local Development Cache is Ready!")
    print("=" * 30)
    print("Redis Endpoint: localhost:6379")
    print("Redis Password: local_dev_password")
    print("")
    print("Environment Variables to set:")
    print("CACHE_BACKEND=local-dev-redis")
    print("LOCAL_REDIS_URL=redis://localhost:6379")
    print("LOCAL_REDIS_PASSWORD=local_dev_password")
    print("")
    print("To stop: docker-compose -f docker-compose.local.yml down")
    print(
        "To view logs: docker-compose -f docker-compose.local.yml logs -f redis-local"
    )


if __name__ == "__main__":
    main()
