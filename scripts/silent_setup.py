#!/usr/bin/env python3
"""Silent setup - only runs what's needed without output"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def setup_env_file():
    """Create .env from .env.example if it doesn't exist"""
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        return True
    return False


def check_venv():
    """Check if virtual environment exists"""
    project_root = Path(__file__).parent.parent
    venv_path = project_root / ".venv"
    return venv_path.exists()


def check_dependencies():
    """Check if dependencies are installed"""
    project_root = Path(__file__).parent.parent
    site_packages = project_root / ".venv" / "lib"
    if site_packages.exists():
        # Find python version directory
        for py_dir in site_packages.iterdir():
            if py_dir.name.startswith("python"):
                mcp_check = py_dir / "site-packages" / "mcp"
                if mcp_check.exists():
                    return True
    return False


def check_keys():
    """Check if RSA keys exist"""
    project_root = Path(__file__).parent.parent
    mock_keys_dir = project_root / "mock_server" / "keys"
    private_key = mock_keys_dir / "private_key.pem"
    public_key = mock_keys_dir / "public_key.pem"
    return private_key.exists() and public_key.exists()


def main():
    """Run minimal setup only if needed"""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Only run full setup if something major is missing
    if not check_venv() or not check_dependencies():
        # Need full setup
        print("🔧 First-time setup needed, setting up automatically...")
        setup_script = Path(__file__).parent / "setup.py"
        subprocess.run([sys.executable, str(setup_script)], check=True)
    else:
        # Just ensure .env exists silently
        setup_env_file()

        # Ensure keys exist for mock server
        if not check_keys():
            mock_keys_dir = project_root / "mock_server" / "keys"
            mock_keys_dir.mkdir(parents=True, exist_ok=True)
            
            # Try to use the Python script first (which handles cryptography module)
            if os.name == 'nt':  # Windows
                python_exe = str(project_root / ".venv" / "Scripts" / "python.exe")
            else:
                python_exe = str(project_root / ".venv" / "bin" / "python")
            
            result = subprocess.run(
                [python_exe, str(project_root / "mock_server" / "scripts" / "generate_rsa_keys.py")],
                cwd=project_root / "mock_server",
                capture_output=True,
            )
            
            # Fall back to openssl if the script fails
            if result.returncode != 0:
                # Generate keys silently with openssl
                subprocess.run(
                    [
                        "openssl",
                        "genrsa",
                        "-out",
                        str(mock_keys_dir / "private_key.pem"),
                        "2048",
                    ],
                    capture_output=True,
                )
                subprocess.run(
                    [
                        "openssl",
                        "rsa",
                        "-in",
                        str(mock_keys_dir / "private_key.pem"),
                        "-pubout",
                        "-out",
                        str(mock_keys_dir / "public_key.pem"),
                    ],
                    capture_output=True,
                )


if __name__ == "__main__":
    main()
