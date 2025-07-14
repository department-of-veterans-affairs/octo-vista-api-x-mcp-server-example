#!/usr/bin/env python3
"""Test Vista configuration detection"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from src.config import get_vista_config

# Load environment variables
load_dotenv()


def main():
    """Test Vista configuration"""
    print("Vista Configuration Test")
    print("=" * 50)

    # Show environment variables
    print("\nEnvironment Variables:")
    print(f"  VISTA_API_BASE_URL: {os.getenv('VISTA_API_BASE_URL', '(not set)')}")
    print(f"  VISTA_AUTH_URL: {os.getenv('VISTA_AUTH_URL', '(not set)')}")
    print(f"  VISTA_API_KEY: {'***' if os.getenv('VISTA_API_KEY') else '(not set)'}")

    # Get configuration
    config = get_vista_config()

    print("\nResolved Configuration:")
    print(f"  Mode: {config['mode'].upper()}")
    print(f"  Base URL: {config['base_url']}")
    print(f"  Auth URL: {config['auth_url']}")
    print(f"  API Key: {'***' if config['api_key'] else '(not set)'}")

    if config["mode"] == "mock":
        print("\n⚠️  Using MOCK server (no production credentials configured)")
        print("   To use production, set VISTA_API_BASE_URL and VISTA_API_KEY")
    else:
        print("\n✅ Using PRODUCTION Vista API")

    return 0


if __name__ == "__main__":
    sys.exit(main())
