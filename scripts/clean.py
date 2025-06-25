#!/usr/bin/env python3
"""Clean up generated files - cross-platform"""

import shutil
from pathlib import Path


def clean_project():
    """Clean up generated files"""
    project_root = Path(__file__).parent.parent
    
    # Directories to remove
    dirs_to_remove = [
        ".venv",
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        ".mypy_cache",
        ".ruff_cache",
    ]
    
    for dir_name in dirs_to_remove:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"Removing {dir_name}...")
            shutil.rmtree(dir_path)
    
    # Remove all __pycache__ directories
    for pycache in project_root.rglob("__pycache__"):
        print(f"Removing {pycache.relative_to(project_root)}")
        shutil.rmtree(pycache)
    
    # Remove all .pyc files
    for pyc_file in project_root.rglob("*.pyc"):
        print(f"Removing {pyc_file.relative_to(project_root)}")
        pyc_file.unlink()
    
    print("✅ Cleaned up generated files")


if __name__ == "__main__":
    clean_project()