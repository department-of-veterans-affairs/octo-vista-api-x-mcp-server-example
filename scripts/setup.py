#!/usr/bin/env python3
"""Setup script for mise - cross-platform"""

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
        print("✅ Created .env from .env.example")
    else:
        print("✅ .env already exists")


def setup_venv():
    """Create virtual environment"""
    print("📦 Creating virtual environment...")
    # Use uv directly, not as a Python module
    result = subprocess.run(["uv", "venv", "--python", "3.12"], 
                          capture_output=True, text=True)
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
    # Use uv directly
    result = subprocess.run(["uv", "pip", "install", "-e", "."], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Dependencies installed")
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
        os.chdir(project_root / "mock_server")
        result = subprocess.run([sys.executable, "scripts/generate_rsa_keys.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Generated RSA keys for mock server")
        else:
            print("⚠️  Failed to generate RSA keys (mock server may not work)")
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