#!/usr/bin/env python3
"""Diagnostic script for Windows Docker issues"""

import os
import socket
import subprocess
import sys
import urllib.error
import urllib.request


def check_port_available(port):
    """Check if a port is available"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        return result != 0  # True if port is free
    except Exception:
        return False


def check_url(url):
    """Check if a URL is accessible"""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200, f"Status: {response.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP Error {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return False, f"URL Error: {e.reason}"
    except Exception as e:
        return False, f"Error: {type(e).__name__}: {e}"


def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return (
            result.stdout.strip()
            if result.returncode == 0
            else f"Error: {result.stderr}"
        )
    except Exception as e:
        return f"Failed to run command: {e}"


def main():
    """Run diagnostics"""
    print("🔍 Windows Docker Diagnostics for Vista Mock Server")
    print("=" * 60)

    # Check OS
    print("\n📋 System Info:")
    print(f"   OS: {os.name} ({sys.platform})")
    print(f"   Python: {sys.version.split()[0]}")

    # Check Docker
    print("\n🐳 Docker Status:")
    docker_version = run_command("docker --version")
    print(f"   Version: {docker_version}")

    docker_running = "running" in run_command("docker info 2>&1")
    print(f"   Status: {'✅ Running' if docker_running else '❌ Not running'}")

    if not docker_running:
        print("\n❌ Docker is not running! Please start Docker Desktop.")
        return

    # Check ports
    print("\n🔌 Port Availability:")
    ports = [8080, 4566, 8001]
    for port in ports:
        is_free = check_port_available(port)
        print(f"   Port {port}: {'✅ Available' if is_free else '❌ In use'}")
        if not is_free and port == 8080:
            print(f"      To find what's using it: netstat -ano | findstr :{port}")

    # Check containers
    print("\n📦 Docker Containers:")
    containers = run_command(
        'docker ps -a --format "table {{.Names}}\\t{{.Status}}" | grep vista'
    )
    if containers:
        print(containers)
    else:
        print("   No Vista containers found")

    # Check specific containers
    print("\n🏥 Vista Mock Server Status:")
    mock_status = run_command(
        'docker ps --filter name=vista-api-x-mock --format "{{.Status}}"'
    )
    print(f"   Container: {mock_status or 'Not found'}")

    if "Up" in mock_status:
        # Check health endpoints
        print("\n🩺 Health Check:")
        urls = [
            "http://localhost:8888/health",
            "http://127.0.0.1:8888/health",
            "http://localhost:8888/",
            "http://127.0.0.1:8888/",
        ]

        for url in urls:
            success, message = check_url(url)
            print(f"   {url}: {'✅' if success else '❌'} {message}")

        # Check logs
        print("\n📜 Recent Container Logs:")
        logs = run_command("docker logs --tail 10 vista-api-x-mock 2>&1")
        print(logs)

    # Network diagnostics
    print("\n🌐 Docker Network:")
    network_info = run_command("docker network ls | grep vista")
    print(f"   Networks: {network_info or 'None found'}")

    # WSL2 check
    print("\n🪟 WSL2 Status:")
    wsl_status = run_command("wsl --status 2>&1")
    if "Default Version: 2" in wsl_status:
        print("   ✅ WSL2 is default")
    else:
        print("   ⚠️  WSL2 might not be configured properly")

    print("\n" + "=" * 60)
    print("🔧 Recommendations:")

    if not docker_running:
        print("1. Start Docker Desktop")

    if not check_port_available(8080):
        print("1. Stop whatever is using port 8080 or change the mock server port")

    if "Up" not in mock_status:
        print("1. Try: docker-compose -f mock_server/docker-compose.yml up -d")
        print("2. Check logs: docker logs vista-api-x-mock")


if __name__ == "__main__":
    main()
