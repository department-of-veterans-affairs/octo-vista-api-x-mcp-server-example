"""
DynamoDB client for authentication and permissions
"""

import json
from pathlib import Path

import aioboto3

from src.auth.models import AuthApplication, Permission, Station
from src.config import settings


class DynamoDBClient:
    """Async DynamoDB client for Vista API X mock"""

    def __init__(self):
        self.session = aioboto3.Session()
        self.table_name = settings.dynamodb_table_name
        self._table = None

    async def _get_table(self):
        """Get DynamoDB table resource"""
        if not self._table:
            async with self.session.resource(
                "dynamodb",
                endpoint_url=settings.aws_endpoint_url,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_default_region,
            ) as dynamodb:
                self._table = await dynamodb.Table(self.table_name)
        return self._table

    async def get_application_by_key(self, app_key: str) -> AuthApplication | None:
        """Get application data by API key"""
        try:
            table = await self._get_table()
            response = await table.get_item(Key={"appKey": app_key})

            if "Item" not in response:
                return None

            item = response["Item"]

            # Convert DynamoDB format to AuthApplication model
            permissions = []
            for perm in item.get("permissions", []):
                permissions.append(
                    Permission(
                        stationNo=perm["stationNo"],
                        userDuz=perm["userDuz"],
                        contextName=perm["contextName"],
                        rpcName=perm["rpcName"],
                    )
                )

            stations = []
            for station in item.get("stations", []):
                stations.append(
                    Station(stationNo=station["stationNo"], userDuz=station["userDuz"])
                )

            return AuthApplication(
                appKey=item["appKey"],
                appName=item["appName"],
                active=item.get("active", True),
                permissions=permissions,
                stations=stations,
                configs=item.get("configs", []),
            )

        except Exception as e:
            print(f"Error getting application by key: {e}")
            # Fallback for test keys when DynamoDB is not available
            if app_key in settings.test_api_keys:
                return AuthApplication(
                    appKey=app_key,
                    appName=(
                        "Test Application"
                        if app_key != "test-wildcard-key-456"
                        else "Test Wildcard Application"
                    ),
                    active=True,
                    permissions=[
                        Permission(
                            stationNo="*", userDuz="*", contextName="*", rpcName="*"
                        )
                    ],
                    stations=[Station(stationNo="*", userDuz="*")],
                    configs=[
                        "ALLOW_VISTA_API_X_TOKEN",
                        "ALLOW_DDR",
                        "ALLOW_ALL_STATIONS",
                        "ALLOW_ALL_RPCS",
                    ],
                )
            return None

    async def create_application(self, app: AuthApplication) -> bool:
        """Create or update application in DynamoDB"""
        try:
            table = await self._get_table()

            # Convert to DynamoDB format
            item = {
                "appKey": app.appKey,
                "appName": app.appName,
                "active": app.active,
                "permissions": [
                    {
                        "stationNo": p.stationNo,
                        "userDuz": p.userDuz,
                        "contextName": p.contextName,
                        "rpcName": p.rpcName,
                    }
                    for p in app.permissions
                ],
                "stations": [
                    {"stationNo": s.stationNo, "userDuz": s.userDuz}
                    for s in app.stations
                ],
                "configs": app.configs,
            }

            await table.put_item(Item=item)
            return True

        except Exception as e:
            print(f"Error creating application: {e}")
            return False

    async def seed_test_data(self):
        """Seed test data from JSON configuration file"""
        # Look for auth config file
        config_paths = [
            Path("/app/config/auth_applications.json"),  # Docker path
            Path("./config/auth_applications.json"),  # Local path
            Path("../config/auth_applications.json"),  # Alternative local path
        ]

        config_file = None
        for path in config_paths:
            if path.exists():
                config_file = path
                break

        if not config_file:
            print("Warning: auth_applications.json not found, using default test data")
            # Fall back to minimal default with LHS RPC CONTEXT
            test_apps = [
                AuthApplication(
                    appKey="test-wildcard-key-456",
                    appName="Test Wildcard Application",
                    active=True,
                    permissions=[
                        Permission(
                            stationNo="*", userDuz="*", contextName="*", rpcName="*"
                        )
                    ],
                    stations=[Station(stationNo="*", userDuz="*")],
                    configs=[
                        "ALLOW_VISTA_API_X_TOKEN",
                        "ALLOW_DDR",
                        "ALLOW_ALL_STATIONS",
                        "ALLOW_ALL_RPCS",
                    ],
                )
            ]
        else:
            # Load from JSON file
            print(f"Loading auth applications from {config_file}")
            with config_file.open() as f:
                config_data = json.load(f)

            test_apps = []
            for app_data in config_data.get("applications", []):
                # Convert permissions
                permissions = [
                    Permission(**perm) for perm in app_data.get("permissions", [])
                ]

                # Convert stations
                stations = [
                    Station(**station) for station in app_data.get("stations", [])
                ]

                # Create application
                app = AuthApplication(
                    appKey=app_data["appKey"],
                    appName=app_data["appName"],
                    active=app_data.get("active", True),
                    permissions=permissions,
                    stations=stations,
                    configs=app_data.get("configs", []),
                )
                test_apps.append(app)

        for app in test_apps:
            await self.create_application(app)
            print(f"Seeded test application: {app.appName}")


# Global DynamoDB client instance
_db_client = None


def get_dynamodb_client() -> DynamoDBClient:
    """Get singleton DynamoDB client"""
    global _db_client
    if _db_client is None:
        _db_client = DynamoDBClient()
    return _db_client
