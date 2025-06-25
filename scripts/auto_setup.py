#!/usr/bin/env python3
"""Auto-setup that runs silently if everything is already set up"""

import subprocess
import sys
from pathlib import Path


def needs_setup():
    """Check if setup is needed"""
    project_root = Path(__file__).parent.parent
    
    # Check if virtual environment exists
    venv_path = project_root / ".venv"
    if not venv_path.exists():
        return True
    
    # Check if .env exists
    env_file = project_root / ".env"
    if not env_file.exists():
        return True
    
    # Check if dependencies are installed by looking for a marker file
    # (Importing them here would fail since we're not in the venv)
    marker_file = project_root / ".venv" / "pip-selfcheck.json"
    if not marker_file.exists():
        return True
    
    return False


def run_setup():
    """Run the setup script"""
    setup_script = Path(__file__).parent / "setup.py"
    subprocess.run([sys.executable, str(setup_script)], check=True)


def main():
    """Check and run setup if needed"""
    if needs_setup():
        print("🔧 First-time setup needed, setting up automatically...")
        run_setup()
    # If setup is not needed, exit silently


if __name__ == "__main__":
    main()