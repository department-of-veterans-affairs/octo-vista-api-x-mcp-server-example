#!/usr/bin/env python3
"""Initialize mock server DynamoDB tables"""

import subprocess
import time
from pathlib import Path


def check_table_exists():
    """Check if the auth table exists"""
    # Try docker first, then podman
    docker_cmd = "docker"
    try:
        subprocess.run(["docker", "version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        docker_cmd = "podman"

    try:
        result = subprocess.run(
            [
                docker_cmd,
                "exec",
                "vista-localstack",
                "awslocal",
                "dynamodb",
                "describe-table",
                "--table-name",
                "AUTH_APPLICATIONS_TABLE_NAME",
                "--region",
                "us-east-1",
            ],
            capture_output=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def create_table():
    """Create the DynamoDB table"""
    print("Creating DynamoDB table...")
    subprocess.run(
        [
            "docker",
            "exec",
            "vista-localstack",
            "awslocal",
            "dynamodb",
            "create-table",
            "--table-name",
            "AUTH_APPLICATIONS_TABLE_NAME",
            "--attribute-definitions",
            "AttributeName=appKey,AttributeType=S",
            "--key-schema",
            "AttributeName=appKey,KeyType=HASH",
            "--provisioned-throughput",
            "ReadCapacityUnits=5,WriteCapacityUnits=5",
            "--region",
            "us-east-1",
        ],
        check=True,
    )


def load_test_data():
    """Load test API keys"""
    print("Loading test data...")

    # Get project root directory
    project_root = Path(__file__).parent.parent
    localstack_dir = project_root / "mock_server" / "localstack"

    # Copy and load each seed file
    seed_files = [
        "dynamodb-seed.json",
        "dynamodb-seed-wildcard.json",
        "dynamodb-seed-limited.json",
    ]

    for seed_file in seed_files:
        # Copy file to container
        subprocess.run(
            [
                "docker",
                "cp",
                str(localstack_dir / seed_file),
                f"vista-localstack:/tmp/{seed_file}",
            ],
            check=True,
        )

        # Load data
        subprocess.run(
            [
                "docker",
                "exec",
                "vista-localstack",
                "awslocal",
                "dynamodb",
                "put-item",
                "--table-name",
                "AUTH_APPLICATIONS_TABLE_NAME",
                "--item",
                f"file:///tmp/{seed_file}",
                "--region",
                "us-east-1",
            ],
            check=True,
        )

    print("✅ Test data loaded successfully")


def main():
    """Initialize mock server database"""
    # Wait a bit for LocalStack to be ready
    time.sleep(2)

    if not check_table_exists():
        print("DynamoDB table not found, initializing...")
        create_table()
        time.sleep(1)
        load_test_data()
    else:
        print("✅ DynamoDB table already exists")


if __name__ == "__main__":
    main()
