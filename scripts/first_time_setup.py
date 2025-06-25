#!/usr/bin/env python3
"""First-time setup script - cross-platform"""

import os
import subprocess
import sys
import shutil
from pathlib import Path


def check_command(command):
    """Check if a command is available"""
    return shutil.which(command) is not None


def run_command(cmd, cwd=None, check=True):
    """Run a command and handle errors"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=check)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False


def main():
    """Run first-time setup"""
    print("🚀 Vista API MCP Server - First Time Setup")
    print("=" * 50)
    print("\n💡 Note: Using mise is easier! Just run: mise install")
    print("   This script is for manual setup without mise.\n")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent
    
    # Check prerequisites
    print("\n📋 Checking prerequisites...")
    
    # Check Python
    if not check_command("python"):
        print("❌ Python not found. Please install Python 3.12+")
        sys.exit(1)
    print("✅ Python found")
    
    # Check uv
    if not check_command("uv"):
        print("❌ uv not found. Installing uv...")
        if sys.platform == "win32":
            # Windows
            run_command("powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
        else:
            # Unix-like
            run_command("curl -LsSf https://astral.sh/uv/install.sh | sh")
        
        if not check_command("uv"):
            print("❌ Failed to install uv. Please install manually: https://github.com/astral-sh/uv")
            sys.exit(1)
    print("✅ uv found")
    
    # Check Docker
    if not check_command("docker"):
        print("⚠️  Docker not found. You'll need Docker to run the mock server.")
        print("   Install from: https://www.docker.com/products/docker-desktop/")
    else:
        print("✅ Docker found")
    
    # Check mise
    if not check_command("mise"):
        print("❌ mise not found. Installing mise...")
        if sys.platform == "win32":
            # Windows
            print("   Please install mise manually:")
            print("   1. Download from: https://github.com/jdx/mise/releases")
            print("   2. Add to PATH")
            print("   Or use: winget install mise")
        else:
            # Unix-like
            run_command("curl https://mise.run | sh")
        
        if not check_command("mise"):
            print("⚠️  mise not installed. You can still use the project without it.")
    else:
        print("✅ mise found")
    
    # Create .env if not exists
    print("\n📄 Setting up environment...")
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env from .env.example")
    else:
        print("✅ .env already exists")
    
    # Install Python dependencies
    print("\n📦 Installing Python dependencies...")
    os.chdir(project_root)
    
    if run_command("uv venv"):
        print("✅ Virtual environment created")
    
    if run_command("uv pip install -e ."):
        print("✅ Dependencies installed")
    else:
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Set up mock server if Docker is available
    if check_command("docker"):
        print("\n🐳 Setting up mock server...")
        mock_dir = project_root / "mock_server"
        
        # Check if RSA keys exist
        keys_dir = mock_dir / "keys"
        if not (keys_dir / "private_key.pem").exists():
            print("🔑 Generating RSA keys...")
            os.chdir(mock_dir)
            if run_command(f"{sys.executable} scripts/generate_rsa_keys.py"):
                print("✅ RSA keys generated")
            else:
                print("❌ Failed to generate RSA keys")
        else:
            print("✅ RSA keys already exist")
    
    # Final instructions
    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    print("\n📖 Next steps:")
    
    if check_command("mise"):
        print("\n  With mise (recommended):")
        print("    mise run dev-with-mock    # Run with mock server")
        print("    mise run dev              # Run with real API")
    else:
        print("\n  Without mise:")
        print("    # Activate virtual environment:")
        if sys.platform == "win32":
            print("    .venv\\Scripts\\activate")
        else:
            print("    source .venv/bin/activate")
        print("\n    # Run development server:")
        print("    python scripts/dev_with_mock.py")
    
    print("\n  Test your setup:")
    print("    python test_setup.py")
    
    print("\n  For more info, see README.md")
    print("\n✨ Happy coding!")


if __name__ == "__main__":
    main()