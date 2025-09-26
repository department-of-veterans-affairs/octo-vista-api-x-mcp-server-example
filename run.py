#!/usr/bin/env python3
"""
Universal runner for Vista API MCP Server.
Works on all platforms (Mac, Windows, Linux) with automatic Docker/Podman detection.
Provides same functionality as mise commands but using native Python tools.
"""

import contextlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, capture_output=False, check=True, shell=False, env=None):
    """Run a command and handle errors"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=check,
            shell=shell,
            env=env or os.environ.copy(),
        )
        return result
    except subprocess.CalledProcessError as e:
        if capture_output:
            print(f"Error: {e.stderr}")
        raise


def detect_container_runtime():
    """Detect whether Docker or Podman is available"""
    # First check for docker
    if shutil.which("docker"):
        try:
            result = run_command(["docker", "version"], capture_output=True)
            # Check if it's actually Podman masquerading as Docker
            if "podman" in result.stdout.lower():
                return "podman"
            return "docker"
        except Exception:
            pass

    # Check for podman
    if shutil.which("podman"):
        return "podman"

    return None


def check_wsl_installed():
    """Check if WSL2 is installed on Windows"""
    try:
        result = subprocess.run(
            ["wsl", "--status"], capture_output=True, text=True, check=False
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def ensure_podman_machine():
    """Ensure Podman machine exists and is running (Windows only)"""
    if platform.system() != "Windows" or not shutil.which("podman"):
        return True

    print("🔧 Checking Podman machine...")

    # Note: Podman uses WSL2 internally but you run everything from Windows
    # You don't need to enter WSL - Podman handles that automatically

    # Check if machine exists
    try:
        result = run_command(
            ["podman", "machine", "list", "--format", "json"], capture_output=True
        )
        machines = json.loads(result.stdout) if result.stdout else []

        machine_exists = any(
            m.get("Name") == "podman-machine-default" for m in machines
        )
        machine_running = any(
            m.get("Name") == "podman-machine-default" and m.get("Running")
            for m in machines
        )

        if not machine_exists:
            print("📦 Creating Podman machine with 8GB RAM...")
            run_command(
                [
                    "podman",
                    "machine",
                    "init",
                    "--cpus",
                    "4",
                    "--memory",
                    "8192",
                    "--disk-size",
                    "50",
                ]
            )
            print("✅ Podman machine created")
            machine_running = False

        if not machine_running:
            print("🚀 Starting Podman machine...")
            run_command(["podman", "machine", "start"])
            print("✅ Podman machine started")

        return True

    except Exception as e:
        print(f"⚠️  Podman machine setup failed: {e}")
        print("   You can manually set it up with:")
        print("   podman machine init --cpus 4 --memory 8192")
        print("   podman machine start")
        return False


def get_python_exe():
    """Get the path to the Python executable in venv"""
    venv_path = Path(".venv")
    if platform.system() == "Windows":
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        python_exe = venv_path / "bin" / "python"

    # If venv doesn't exist, use current Python
    if not python_exe.exists():
        return sys.executable

    return str(python_exe)


def get_pip_exe():
    """Get the path to pip in venv or use uv pip"""
    # Check if uv is available and should be used
    if shutil.which("uv"):
        return ["uv", "pip"]

    venv_path = Path(".venv")
    if platform.system() == "Windows":
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        pip_exe = venv_path / "bin" / "pip"

    # If pip exists in venv, use it
    if pip_exe.exists():
        return [str(pip_exe)]

    # Fall back to system pip
    return [sys.executable, "-m", "pip"]


def start_windows_background_process(popen_args, env, log_file):
    """Start a background process on Windows with proper flags"""
    if hasattr(subprocess, "STARTUPINFO"):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 0)
        create_new_console = getattr(subprocess, "CREATE_NEW_CONSOLE", None)
        if create_new_console is not None:
            subprocess.Popen(
                popen_args,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=env,
                startupinfo=startupinfo,
                creationflags=create_new_console,
            )
        else:
            subprocess.Popen(
                popen_args,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=env,
                startupinfo=startupinfo,
            )
    else:
        subprocess.Popen(
            popen_args,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env=env,
        )


def check_windows_requirements():
    """Check Windows-specific requirements for Python development"""
    if platform.system() != "Windows":
        return True

    issues_found = False

    # Check for Windows Store Python (common cause of WinError 1920)
    python_path = sys.executable
    if "WindowsApps" in python_path:
        print("❌ Detected Windows Store Python installation!")
        print(
            "   The Windows Store version has permission issues with virtual environments."
        )
        print("\n🔧 Solution:")
        print("   1. Uninstall Python from Microsoft Store")
        print("   2. Download Python from https://python.org/downloads/")
        print("   3. During installation, check 'Add Python to PATH'")
        issues_found = True

    # Check PowerShell execution policy
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-ExecutionPolicy -Scope CurrentUser"],
            capture_output=True,
            text=True,
            check=False,
        )
        policy = result.stdout.strip()
        if policy in ["Restricted", "AllSigned"]:
            print("\n⚠️  PowerShell execution policy is too restrictive: " + policy)
            print("   This will prevent virtual environment activation.")
            print("\n🔧 To fix (run in PowerShell):")
            print(
                "   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
            )
            print("\n   Or for this session only:")
            print("   Set-ExecutionPolicy Unrestricted -Scope Process")
            issues_found = True
    except Exception:
        # PowerShell not available or other error
        pass

    return not issues_found


def setup_venv():
    """Create and setup virtual environment"""
    venv_path = Path(".venv")

    # Create venv if it doesn't exist
    if not venv_path.exists():
        print("📦 Creating virtual environment...")

        # Check Windows-specific requirements first
        if not check_windows_requirements():
            print("\n❌ Please fix the above issues before continuing.")
            sys.exit(1)

        # Check if uv is available and prefer it
        if shutil.which("uv"):
            print("  Using uv to create virtual environment...")
            try:
                run_command(["uv", "venv", ".venv", "--python", "3.12"])
                print("✅ Virtual environment created with uv")
            except Exception:
                # Fall back to standard venv
                print("  Falling back to standard venv...")
                try:
                    # Use subprocess directly for better error handling
                    result = subprocess.run(
                        [sys.executable, "-m", "venv", ".venv"],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode != 0:
                        raise Exception(result.stderr)
                    print("✅ Virtual environment created with venv module")
                except Exception as e:
                    if "WinError 1920" in str(e) or "cannot be accessed" in str(e):
                        print(f"❌ Failed to create venv: {e}")
                        print("\n🔍 This is likely due to Windows Store Python.")
                        print("   Please install Python from python.org instead.")
                    else:
                        print(f"❌ Failed to create venv: {e}")
                    sys.exit(1)
        else:
            # Use standard venv module
            try:
                # Use subprocess for better control
                result = subprocess.run(
                    [sys.executable, "-m", "venv", ".venv"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    raise Exception(result.stderr)
                print("✅ Virtual environment created")
            except Exception as e:
                if "WinError 1920" in str(e) or "cannot be accessed" in str(e):
                    print(f"❌ Failed to create venv: {e}")
                    print("\n🔍 This is a Windows Store Python issue.")
                    print("\n🔧 Solution:")
                    print("   1. Uninstall Python from Microsoft Store")
                    print("   2. Download Python from https://python.org/downloads/")
                    print("   3. During installation, check 'Add Python to PATH'")
                else:
                    print(f"❌ Failed to create venv: {e}")
                sys.exit(1)
    else:
        print("✅ Virtual environment already exists")

    # Get pip command (might be a list like ["uv", "pip"])
    pip_cmd = get_pip_exe()

    # Upgrade pip first (skip for uv)
    if pip_cmd[0] != "uv":
        print("📦 Upgrading pip...")
        # On Windows, use python -m pip to upgrade pip to avoid conflicts
        if platform.system() == "Windows":
            python_exe = get_python_exe()
            with contextlib.suppress(subprocess.CalledProcessError):
                # Pip upgrade often returns non-zero on Windows even when successful
                run_command(
                    [python_exe, "-m", "pip", "install", "--upgrade", "pip"],
                    capture_output=True,
                )
        else:
            with contextlib.suppress(subprocess.CalledProcessError):
                run_command(
                    pip_cmd + ["install", "--upgrade", "pip"], capture_output=True
                )

    # Install dependencies
    print("📦 Installing dependencies from requirements.txt...")
    run_command(pip_cmd + ["install", "-r", "requirements.txt"])

    # Install package in editable mode
    print("📦 Installing package in editable mode...")
    run_command(pip_cmd + ["install", "-e", "."])

    # Create .env from .env.example if needed
    env_file = Path(".env")
    env_example = Path(".env.example")
    if not env_file.exists() and env_example.exists():
        shutil.copy2(env_example, env_file)
        print("✅ Created .env from .env.example")

    # Generate RSA keys for mock server if needed (after dependencies are installed)
    setup_mock_keys()

    print("\n✅ Setup complete!")


def setup_mock_keys():
    """Generate RSA keys for mock server if needed"""
    keys_dir = Path("mock_server") / "keys"
    private_key = keys_dir / "private_key.pem"

    if not private_key.exists():
        print("🔑 Generating RSA keys for mock server...")
        keys_dir.mkdir(parents=True, exist_ok=True)

        python_exe = get_python_exe()

        # Check if the generate script exists
        generate_script = Path("mock_server") / "scripts" / "generate_rsa_keys.py"
        if not generate_script.exists():
            print("⚠️  RSA key generation script not found")
            print("   Mock server will generate keys on first run")
            return

        # Save current directory and change to mock_server
        original_dir = os.getcwd()
        os.chdir(Path("mock_server"))

        try:
            result = subprocess.run(
                [python_exe, "scripts/generate_rsa_keys.py"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                print("✅ Generated RSA keys for mock server")
            else:
                print(
                    "⚠️  RSA key generation failed (mock server will generate on first run)"
                )
                if result.stderr:
                    print(f"   Error: {result.stderr[:200]}")
        except Exception:
            print("⚠️  Could not generate RSA keys now (mock server will handle it)")
        finally:
            os.chdir(original_dir)
    else:
        print("✅ RSA keys already exist")


def run_dev():
    """Run MCP server in development mode (stdio + HTTP)"""
    print("🚀 Starting MCP transports...")
    print("")
    print("📍 Available endpoints:")
    print("  📡 stdio: mcp dev server (for Claude Desktop)")
    print("  🌐 HTTP: http://localhost:8000/mcp")
    print("")
    print("🎯 Starting servers in background...")

    # Create logs directory
    Path("logs").mkdir(exist_ok=True)

    # Start HTTP server in background
    env = os.environ.copy()
    env["VISTA_MCP_HTTP_PORT"] = "8000"

    # Run HTTP server in background (platform-specific)
    log_path = Path("logs") / "http.log"
    with open(log_path, "w") as log_file:
        if platform.system() == "Windows":
            # Windows-specific background process
            popen_args = [get_python_exe(), "http_server.py"]
            start_windows_background_process(popen_args, env, log_file)
        else:
            # Unix-like systems - use subprocess.Popen instead of os.system
            if shutil.which("uv"):
                popen_args = ["uv", "run", "python", "http_server.py"]
            else:
                popen_args = [get_python_exe(), "http_server.py"]
            subprocess.Popen(
                popen_args,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=env,
            )

    # Wait for servers to start
    time.sleep(3)

    print("✅ Background HTTP server started (logs in logs/http.log)")
    print("🏃 Starting stdio MCP dev server (main)...")
    print("   Use Ctrl+C to stop all servers")

    # Run stdio server in foreground - with mcp dev (includes inspector)
    if shutil.which("uv"):
        run_command(["uv", "run", "mcp", "dev", "server.py:server"])
    else:
        venv_path = Path(".venv")
        if platform.system() == "Windows":
            mcp_exe = venv_path / "Scripts" / "mcp.exe"
        else:
            mcp_exe = venv_path / "bin" / "mcp"

        if not mcp_exe.exists():
            print("❌ MCP not installed. Run 'python run.py setup' first")
            sys.exit(1)

        run_command([str(mcp_exe), "dev", "server.py:server"])


def run_dev_with_mock():
    """Run MCP server with mock Vista API (both stdio + HTTP transports)"""
    # Ensure Podman machine is running on Windows
    runtime = detect_container_runtime()
    if (
        runtime == "podman"
        and platform.system() == "Windows"
        and not ensure_podman_machine()
    ):
        print("⚠️  Podman machine setup failed, continuing anyway...")

    # Start mock server if needed
    python_exe = get_python_exe()
    try:
        run_command([python_exe, "scripts/start_mock_if_needed.py"])
    except subprocess.CalledProcessError:
        print("⚠️  Failed to start mock server, continuing anyway...")

    # Now run the same as dev (both transports)
    run_dev()


def run_dev_with_mock_and_redis():
    """Run MCP server with mock Vista API and Redis caching"""
    # Ensure Podman machine is running on Windows
    runtime = detect_container_runtime()
    if (
        runtime == "podman"
        and platform.system() == "Windows"
        and not ensure_podman_machine()
    ):
        print("⚠️  Podman machine setup failed, continuing anyway...")

    # Start mock server if needed (which includes Redis in docker-compose)
    python_exe = get_python_exe()
    try:
        run_command([python_exe, "scripts/start_mock_if_needed.py"])
    except subprocess.CalledProcessError:
        print("⚠️  Failed to start mock server, continuing anyway...")

    # Set Redis cache environment variables
    env = os.environ.copy()
    env["CACHE_BACKEND"] = "local-dev-redis"
    env["LOCAL_CACHE_BACKEND_TYPE"] = "elasticache"
    env["LOCAL_REDIS_URL"] = "redis://localhost:6379"
    env["LOCAL_REDIS_FALLBACK"] = "true"
    env["VISTA_MCP_HTTP_PORT"] = "8000"
    env["ENABLE_CONSOLE_LOGGING"] = "true"

    print("🚀 Starting MCP transports with Redis caching...")
    print("")
    print("📍 Available endpoints:")
    print("  📡 stdio: mcp dev server (for Claude Desktop)")
    print("  🌐 HTTP: http://localhost:8000/mcp")
    print("  🔴 Redis: redis://localhost:6379")
    print("")
    print("🎯 Starting servers in background...")

    # Create logs directory
    Path("logs").mkdir(exist_ok=True)

    # Start HTTP server in background with Redis environment
    log_path = Path("logs") / "http.log"
    with open(log_path, "w") as log_file:
        if platform.system() == "Windows":
            # Windows-specific background process
            popen_args = [get_python_exe(), "http_server.py"]
            start_windows_background_process(popen_args, env, log_file)
        else:
            # Unix-like systems
            if shutil.which("uv"):
                popen_args = ["uv", "run", "python", "http_server.py"]
            else:
                popen_args = [get_python_exe(), "http_server.py"]
            subprocess.Popen(
                popen_args,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=env,
            )

    # Wait for servers to start
    time.sleep(3)

    print(
        "✅ Background HTTP server started with Redis caching (logs in logs/http.log)"
    )
    print("🏃 Starting stdio MCP dev server (main)...")
    print("   Use Ctrl+C to stop all servers")

    # Run stdio server in foreground with Redis environment
    if shutil.which("uv"):
        run_command(["uv", "run", "mcp", "dev", "server.py:server"], env=env)
    else:
        venv_path = Path(".venv")
        if platform.system() == "Windows":
            mcp_exe = venv_path / "Scripts" / "mcp.exe"
        else:
            mcp_exe = venv_path / "bin" / "mcp"

        if not mcp_exe.exists():
            print("❌ MCP not installed. Run 'python run.py setup' first")
            sys.exit(1)

        run_command([str(mcp_exe), "dev", "server.py:server"], env=env)


def run_test():
    """Run tests with pytest"""
    print("🧪 Running tests...")
    python_exe = get_python_exe()

    try:
        run_command([python_exe, "-m", "pytest"])
    except subprocess.CalledProcessError:
        print("❌ Tests failed")
        sys.exit(1)


def run_lint():
    """Run linting and formatting"""
    print("🔍 Running code quality checks...")

    # Check if uv is available
    uv_path = shutil.which("uv")
    if uv_path:
        # Use uv run (same as mise)
        print("  Running black formatter...")
        try:
            run_command(["uv", "run", "black", "."])
        except subprocess.CalledProcessError:
            print("  ⚠️  Black formatting failed")

        print("  Running ruff linter...")
        try:
            run_command(["uv", "run", "ruff", "check", "--fix", "."])
        except subprocess.CalledProcessError:
            print("  ⚠️  Ruff check failed")

        print("  Running mypy type checker...")
        try:
            run_command(["uv", "run", "mypy", "."])
        except subprocess.CalledProcessError:
            print("  ⚠️  Mypy check failed")
    else:
        # Fallback to direct python -m calls
        python_exe = get_python_exe()

        print("  Running black formatter...")
        try:
            run_command([python_exe, "-m", "black", "."])
        except subprocess.CalledProcessError:
            print("  ⚠️  Black formatting failed or not installed")

        print("  Running ruff linter...")
        try:
            run_command([python_exe, "-m", "ruff", "check", "--fix", "."])
        except subprocess.CalledProcessError:
            print("  ⚠️  Ruff check failed or not installed")

        print("  Running mypy type checker...")
        try:
            run_command([python_exe, "-m", "mypy", "."])
        except subprocess.CalledProcessError:
            print("  ⚠️  Mypy check failed or not installed")

    print("✅ Linting complete")


def run_setup():
    """Run full setup using scripts/setup.py"""
    setup_script = Path(__file__).parent / "scripts" / "setup.py"
    if not setup_script.exists():
        print("❌ setup.py script not found")
        sys.exit(1)

    print("🔧 Running setup script...")
    run_command([sys.executable, str(setup_script)])
    print("✅ Setup complete")


def run_check():
    """Run lint/format/type/test checks without modifying files"""
    print("🧪 Running full check suite (ruff, black --check, mypy, pytest)...")

    use_uv = shutil.which("uv") is not None
    python_exe = get_python_exe()

    if use_uv:
        commands = [
            ("Ruff", ["uv", "run", "ruff", "check"]),
            ("Black --check", ["uv", "run", "black", "--check", "."]),
            ("Mypy", ["uv", "run", "mypy"]),
            ("Pytest", ["uv", "run", "pytest"]),
        ]
    else:
        commands = [
            ("Ruff", [python_exe, "-m", "ruff", "check"]),
            ("Black --check", [python_exe, "-m", "black", "--check", "."]),
            ("Mypy", [python_exe, "-m", "mypy"]),
            ("Pytest", [python_exe, "-m", "pytest"]),
        ]

    for label, cmd in commands:
        print(f"  Running {label}...")
        run_command(cmd)

    print("✅ All checks passed")


def stop_mock():
    """Stop mock server containers"""
    print("🛑 Stopping mock server...")

    runtime = detect_container_runtime()
    if not runtime:
        print("❌ No container runtime (Docker/Podman) found")
        return

    # Change to mock_server directory
    original_dir = os.getcwd()
    mock_dir = Path("mock_server")

    if mock_dir.exists():
        os.chdir(mock_dir)

        try:
            if runtime == "podman" and platform.system() == "Windows":
                # Use podman commands directly
                run_command(
                    ["podman", "stop", "vista-localstack"],
                    capture_output=True,
                    check=False,
                )
                run_command(
                    ["podman", "stop", "vista-api-x-mock"],
                    capture_output=True,
                    check=False,
                )
                run_command(
                    ["podman", "stop", "vista-dynamodb-admin"],
                    capture_output=True,
                    check=False,
                )
            else:
                # Use docker-compose
                env = os.environ.copy()
                env["COMPOSE_PROJECT_NAME"] = "vista-mock"
                run_command([runtime, "compose", "down"], env=env)

            print("✅ Mock server stopped")
        except Exception:
            print("⚠️  Failed to stop mock server")
        finally:
            os.chdir(original_dir)


def run_logs():
    """View mock server logs"""
    print("📋 Viewing mock server logs...")

    runtime = detect_container_runtime()
    if not runtime:
        print("❌ No container runtime (Docker/Podman) found")
        return

    # Change to mock_server directory
    original_dir = os.getcwd()
    mock_dir = Path("mock_server")

    if mock_dir.exists():
        os.chdir(mock_dir)

        try:
            env = os.environ.copy()
            env["COMPOSE_PROJECT_NAME"] = "vista-mock"
            run_command([runtime, "compose", "logs", "-f"], env=env)
        except KeyboardInterrupt:
            pass
        finally:
            os.chdir(original_dir)


def run_http():
    """Run MCP server in HTTP mode"""
    print("🚀 Starting Streamable HTTP server...")
    print("📍 MCP endpoint: http://localhost:8000/mcp")
    print("🔧 Configure your client with:")
    print("  Transport: streamable-http")
    print("  URL: http://localhost:8000/mcp")
    print("")

    python_exe = get_python_exe()

    # Set environment variable for HTTP port
    env = os.environ.copy()
    env["VISTA_MCP_HTTP_PORT"] = "8000"

    # Run the HTTP server
    run_command([python_exe, "http_server.py"], env=env)


def run_http_with_mock():
    """Run HTTP server with mock"""
    # Ensure Podman machine is running on Windows
    runtime = detect_container_runtime()
    if (
        runtime == "podman"
        and platform.system() == "Windows"
        and not ensure_podman_machine()
    ):
        print("⚠️  Podman machine setup failed, continuing anyway...")

    # Start mock server if needed
    print("🚀 Starting mock server if needed...")
    python_exe = get_python_exe()

    try:
        run_command([python_exe, "scripts/start_mock_if_needed.py"])
    except subprocess.CalledProcessError:
        print("⚠️  Failed to start mock server, continuing anyway...")

    # Run the HTTP server
    run_http()


def stop_servers():
    """Stop any background MCP servers"""
    print("🛑 Stopping background MCP servers...")

    if platform.system() == "Windows":
        # Windows-specific process killing
        # Kill Python processes running our servers
        subprocess.run(
            ["taskkill", "/F", "/IM", "python.exe", "/FI", "IMAGENAME eq python.exe"],
            capture_output=True,
            check=False,
        )
        # Also try with windowtitle
        subprocess.run(
            ["taskkill", "/F", "/FI", "WINDOWTITLE eq *http_server*"],
            capture_output=True,
            check=False,
        )
    else:
        # Unix-like systems
        result = subprocess.run(
            ["pkill", "-f", "http_server.py"],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            print("   (no http_server.py processes found)")

        result = subprocess.run(
            ["pkill", "-f", "server.py:server"],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            print("   (no mcp dev processes found)")

    print("✅ Background servers stopped")


def check_windows():
    """Check all Windows requirements and provide fixes"""
    if platform.system() != "Windows":
        print("This command is only for Windows systems.")
        return

    print("🔍 Checking Windows development environment...\n")

    all_good = True

    # Check Python installation
    print("1️⃣  Python Installation:")
    python_path = sys.executable
    if "WindowsApps" in python_path:
        print("   ❌ Using Windows Store Python (has permission issues)")
        print("      Fix: Install Python from python.org instead")
        all_good = False
    else:
        print(f"   ✅ Using regular Python: {python_path}")

    # Check PowerShell execution policy
    print("\n2️⃣  PowerShell Execution Policy:")
    try:
        # Try different ways to invoke PowerShell on Windows
        powershell_cmds = [
            ["powershell.exe", "-Command", "Get-ExecutionPolicy -Scope CurrentUser"],
            ["pwsh.exe", "-Command", "Get-ExecutionPolicy -Scope CurrentUser"],
            ["powershell", "-Command", "Get-ExecutionPolicy -Scope CurrentUser"],
        ]

        policy = None
        for cmd in powershell_cmds:
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=False, shell=False
                )
                if result.returncode == 0:
                    policy = result.stdout.strip()
                    break
            except FileNotFoundError:
                continue

        if policy:
            if policy in ["Restricted", "AllSigned"]:
                print(f"   ❌ Too restrictive: {policy}")
                print("      Fix: Run in PowerShell:")
                print(
                    "      Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
                )
                all_good = False
            elif policy in ["Undefined", "Unrestricted", "RemoteSigned", "Bypass"]:
                print(f"   ✅ Policy is OK: {policy}")
                if policy == "Undefined":
                    print(
                        "      (Undefined means no policy set, which allows scripts to run)"
                    )
            else:
                print(f"   ⚠️  Unknown policy: {policy}")
                print(
                    "      This might work, but consider setting to RemoteSigned if you have issues"
                )
        else:
            print("   ⚠️  Could not check execution policy")
            print(
                "      To check manually, run: Get-ExecutionPolicy -Scope CurrentUser"
            )
    except Exception as e:
        print(f"   ⚠️  Could not check: {e}")

    # Check WSL2 for Podman (Podman uses it internally but you work in Windows)
    print("\n3️⃣  WSL2 (used internally by Podman):")
    if check_wsl_installed():
        print("   ✅ WSL2 is installed (Podman will use it in the background)")
        print("      Note: You run everything from Windows PowerShell, not inside WSL")
    else:
        print("   ⚠️  WSL2 not installed (only needed if using Podman)")
        print("      If you want to use Podman: Run as Administrator: wsl --install")
        print("      Alternative: Use Docker Desktop instead")

    # Check Podman
    print("\n4️⃣  Container Runtime:")
    if shutil.which("podman"):
        print("   ✅ Podman is installed")
    elif shutil.which("docker"):
        print("   ✅ Docker is installed")
    else:
        print("   ⚠️  No container runtime found")
        print("      Optional: Install Podman Desktop from podman.io")

    # Summary
    print("\n" + "=" * 50)
    if all_good:
        print("✅ All checks passed! You can run: python run.py setup")
    else:
        print("❌ Please fix the issues above before running setup")


def show_help():
    """Show help message"""
    print(
        """
Vista API MCP Server - Universal Runner
=======================================

Usage: python run.py <command>

Commands:
  setup                    - Setup virtual environment and install dependencies
  check                    - Run lint/format/type/test checks (no auto-fixes)
  dev                      - Run MCP server (stdio + HTTP, with inspector)
  dev-with-mock            - Same as dev but with mock Vista API
  dev-with-mock-and-redis  - Same as dev-with-mock but with Redis caching
  test                     - Run tests with pytest
  lint                     - Run code quality checks (black, ruff, mypy)
  stop-mock                - Stop mock server containers
  stop-servers             - Stop any background MCP servers
  logs                     - View mock server logs
  http                     - Run HTTP server only (no stdio)
  http-with-mock           - Run HTTP server with mock Vista API
  check-windows            - Check Windows development requirements
  help                     - Show this help message

Examples:
  python run.py setup          # First time setup
  python run.py dev            # Start development server
  python run.py dev-with-mock  # Start with mock server
  python run.py test           # Run tests

Windows users: Run 'python run.py check-windows' first to verify your setup.

This script works on all platforms (Mac, Windows, Linux) and automatically
detects whether to use Docker or Podman for the mock server.
    """
    )


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    command = sys.argv[1].lower()

    commands = {
        "setup": run_setup,
        "check": run_check,
        "dev": run_dev,
        "dev-with-mock": run_dev_with_mock,
        "dev-with-mock-and-redis": run_dev_with_mock_and_redis,
        "test": run_test,
        "lint": run_lint,
        "stop-mock": stop_mock,
        "stop-servers": stop_servers,
        "logs": run_logs,
        "http": run_http,
        "http-with-mock": run_http_with_mock,
        "check-windows": check_windows,
        "help": show_help,
    }

    if command in commands:
        try:
            commands[command]()
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)
    else:
        print(f"❌ Unknown command: {command}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
