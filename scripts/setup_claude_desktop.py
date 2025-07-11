#!/usr/bin/env python3
"""Helper script to set up Claude Desktop configuration"""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_claude_config_path():
    """Get Claude Desktop config path for current platform"""
    system = platform.system()

    if system == "Darwin":  # macOS
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json"
        )
    elif system == "Windows":
        return Path(os.environ["APPDATA"]) / "Claude" / "claude_desktop_config.json"
    else:  # Linux
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def find_uv():
    """Find uv executable"""
    # Try common locations
    uv_path = shutil.which("uv")
    if uv_path:
        return uv_path

    # Check common installation paths
    paths = [
        Path.home() / ".local" / "bin" / "uv",
        Path.home() / ".cargo" / "bin" / "uv",
        Path("/usr/local/bin/uv"),
    ]

    for path in paths:
        if path.exists():
            return str(path)

    return None


def main():
    """Set up Claude Desktop configuration"""
    print("🚀 Vista API MCP Server - Claude Desktop Setup")
    print("=" * 50)

    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.resolve()

    # Find uv
    uv_path = find_uv()
    if not uv_path:
        print("❌ Could not find 'uv' command.")
        print(
            "Please install it first: curl -LsSf https://astral.sh/uv/install.sh | sh"
        )
        sys.exit(1)

    print(f"✅ Found uv at: {uv_path}")
    print(f"✅ Project root: {project_root}")

    # Get config path
    config_path = get_claude_config_path()
    print(f"📝 Config file: {config_path}")

    # Load existing config or create new
    if config_path.exists():
        print("📖 Loading existing configuration...")
        with open(config_path) as f:
            config = json.load(f)
    else:
        print("📄 Creating new configuration...")
        config = {}
        config_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure mcpServers exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Create Vista API config
    vista_config = {
        "command": uv_path,
        "args": ["--directory", str(project_root), "run", "python", "server.py"],
        "env": {
            "VISTA_API_BASE_URL": "http://localhost:8080",
            "VISTA_API_KEY": "test-wildcard-key-456",
            "DEFAULT_STATION": "500",
            "DEFAULT_DUZ": "10000000219",
        },
    }

    # Check if already configured
    if "vista-api" in config["mcpServers"]:
        print("\n⚠️  Vista API server already configured!")
        response = input("Replace existing configuration? [y/N]: ").lower()
        if response != "y":
            print("❌ Setup cancelled.")
            return

    # Add configuration
    config["mcpServers"]["vista-api"] = vista_config

    # Save config
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print("\n✅ Configuration saved!")

    # Show next steps
    print("\n📋 Next steps:")
    print("1. Make sure the mock server is running:")
    print("   mise run dev-with-mock")
    print("2. Restart Claude Desktop completely (Cmd+Q / Alt+F4)")
    print("3. Start a new conversation and try:")
    print('   "Can you search for patients with last name ANDERSON?"')

    # Offer to start mock server
    print("\n" + "=" * 50)
    response = input("Start mock server now? [Y/n]: ").lower()
    if response != "n":
        os.chdir(project_root)
        subprocess.run(["mise", "run", "dev-with-mock"])


if __name__ == "__main__":
    main()
