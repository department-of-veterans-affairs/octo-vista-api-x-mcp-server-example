#!/usr/bin/env python3
"""Setup script for mise - cross-platform"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def is_in_container():
    """Check if running inside a container"""
    return (
        os.path.exists("/.dockerenv") or os.environ.get("REMOTE_CONTAINERS") == "true"
    )


def setup_env_file():
    """Create .env from .env.example if it doesn't exist"""
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    if not env_file.exists() and env_example.exists():
        # Use copy2 or copyfile to avoid permission issues on Windows mounts
        try:
            shutil.copy2(env_example, env_file)
        except (PermissionError, OSError):
            # Fall back to simple file copy without preserving metadata
            shutil.copyfile(env_example, env_file)
        print("✅ Created .env from .env.example")
    else:
        print("✅ .env already exists")


def setup_venv():
    """Create virtual environment"""
    print("📦 Creating virtual environment...")

    # Check if we're in a container (devcontainer environment)
    in_container = is_in_container()

    if in_container:
        # In container, create venv in /tmp to avoid permission issues
        venv_path = "/tmp/workspace-venv"
        env = os.environ.copy()
        env["UV_CACHE_DIR"] = "/tmp/uv-cache"
        result = subprocess.run(
            ["uv", "venv", venv_path, "--python", "3.12"],
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode == 0:
            # Create symlink from .venv to actual venv location
            project_root = Path(__file__).parent.parent
            venv_link = project_root / ".venv"
            if venv_link.is_symlink():
                venv_link.unlink()
            elif venv_link.exists():
                # If it's a regular file/dir, remove it
                if venv_link.is_dir():
                    shutil.rmtree(venv_link)
                else:
                    venv_link.unlink()
            try:
                # If symlink fails, just use the /tmp location directly
                venv_link.symlink_to(venv_path)
            except (PermissionError, OSError) as e:
                print(
                    f"⚠️  Warning: Failed to create symlink {venv_link} -> {venv_path}: {e}"
                )
                print("    The virtual environment is available at /tmp/workspace-venv")
    else:
        # Normal environment
        result = subprocess.run(
            ["uv", "venv", "--python", "3.12"], capture_output=True, text=True
        )

    if result.returncode == 0:
        print("✅ Virtual environment created")
    else:
        print("❌ Failed to create virtual environment")
        print(result.stderr)
        return False
    return True


def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")

    # Check if we're in a container
    in_container = is_in_container()

    if in_container:
        # In container, use venv from /tmp and different cache directory
        venv_path = "/tmp/workspace-venv"
        env = os.environ.copy()
        env["UV_CACHE_DIR"] = "/tmp/uv-cache"
        env["VIRTUAL_ENV"] = venv_path
        result = subprocess.run(
            ["uv", "pip", "install", "--python", venv_path, "-e", "."],
            capture_output=True,
            text=True,
            env=env,
        )
    else:
        # Normal environment
        result = subprocess.run(
            ["uv", "pip", "install", "-e", "."], capture_output=True, text=True
        )

    if result.returncode == 0:
        print("✅ Dependencies installed")
        # Also ensure cryptography is installed for the mock server
        if in_container:
            env = os.environ.copy()
            env["UV_CACHE_DIR"] = "/tmp/uv-cache"
            venv_path = "/tmp/workspace-venv"
            env["VIRTUAL_ENV"] = venv_path
            subprocess.run(
                ["uv", "pip", "install", "--python", venv_path, "cryptography"],
                capture_output=True,
                text=True,
                env=env,
            )
        else:
            subprocess.run(
                ["uv", "pip", "install", "cryptography"], capture_output=True, text=True
            )
    else:
        print("❌ Failed to install dependencies")
        print(result.stderr)
        return False
    return True


def setup_mock_keys():
    """Generate RSA keys for mock server if needed"""
    project_root = Path(__file__).parent.parent
    keys_dir = project_root / "mock_server" / "keys"
    private_key = keys_dir / "private_key.pem"

    if not private_key.exists():
        print("🔑 Generating RSA keys for mock server...")

        # Ensure keys directory exists
        keys_dir.mkdir(parents=True, exist_ok=True)

        # Check if we're in a container
        in_container = is_in_container()

        if in_container:
            # In container, use the system python3 or current python
            python_exe = sys.executable
        elif os.name == "nt":  # Windows
            python_exe = str(project_root / ".venv" / "Scripts" / "python.exe")
        else:
            python_exe = str(project_root / ".venv" / "bin" / "python")

        # Save current directory and change to mock_server
        original_dir = os.getcwd()
        os.chdir(project_root / "mock_server")

        # First, try to install cryptography if needed
        if in_container:
            env = os.environ.copy()
            env["UV_CACHE_DIR"] = "/tmp/uv-cache"
            subprocess.run(
                [
                    "uv",
                    "pip",
                    "install",
                    "--python",
                    "/tmp/workspace-venv",
                    "cryptography",
                ],
                capture_output=True,
                text=True,
                env=env,
            )

        result = subprocess.run(
            [python_exe, "scripts/generate_rsa_keys.py"],
            capture_output=True,
            text=True,
        )

        # Change back to original directory
        os.chdir(original_dir)

        if result.returncode == 0:
            print("✅ Generated RSA keys for mock server")
        else:
            print("⚠️  Failed to generate RSA keys (mock server may not work)")
            if result.stderr:
                print(result.stderr)
    else:
        print("✅ RSA keys already exist")


def main():
    """Run setup tasks"""
    print("🚀 Setting up Vista API MCP Server...")
    print("=" * 50)

    # Setup tasks
    setup_env_file()

    if setup_venv() and install_dependencies():
        setup_mock_keys()
        print("\n" + "=" * 50)
        print("✅ Setup complete! Run: mise run dev-with-mock")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
