"""
DynamoDB client for authentication and permissions
"""

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
                stations.append(Station(stationNo=station["stationNo"], userDuz=station["userDuz"]))

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
                    appName=("Test Application" if app_key != "test-wildcard-key-456" else "Test Wildcard Application"),
                    active=True,
                    permissions=[Permission(stationNo="*", userDuz="*", contextName="*", rpcName="*")],
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
                "stations": [{"stationNo": s.stationNo, "userDuz": s.userDuz} for s in app.stations],
                "configs": app.configs,
            }

            await table.put_item(Item=item)
            return True

        except Exception as e:
            print(f"Error creating application: {e}")
            return False

    async def seed_test_data(self):
        """Seed test data for development"""
        test_apps = [
            AuthApplication(
                appKey="test-standard-key-123",
                appName="Test Standard Application",
                active=True,
                permissions=[
                    Permission(
                        stationNo="500",
                        userDuz="10000000219",
                        contextName="OR CPRS GUI CHART",
                        rpcName="*",
                    ),
                    Permission(
                        stationNo="500",
                        userDuz="10000000219",
                        contextName="VPR APPLICATION PROXY",
                        rpcName="*",
                    ),
                    Permission(
                        stationNo="508",
                        userDuz="10000000220",
                        contextName="OR CPRS GUI CHART",
                        rpcName="*",
                    ),
                    Permission(
                        stationNo="640",
                        userDuz="10000000221",
                        contextName="SDESRPC",
                        rpcName="*",
                    ),
                ],
                stations=[
                    Station(stationNo="500", userDuz="10000000219"),
                    Station(stationNo="508", userDuz="10000000220"),
                    Station(stationNo="640", userDuz="10000000221"),
                ],
                configs=["ALLOW_VISTA_API_X_TOKEN", "ALLOW_DDR"],
            ),
            AuthApplication(
                appKey="test-wildcard-key-456",
                appName="Test Wildcard Application",
                active=True,
                permissions=[Permission(stationNo="*", userDuz="*", contextName="*", rpcName="*")],
                stations=[Station(stationNo="*", userDuz="*")],
                configs=["ALLOW_VISTA_API_X_TOKEN", "ALLOW_DDR"],
            ),
            AuthApplication(
                appKey="test-limited-key-789",
                appName="Test Limited Application",
                active=True,
                permissions=[
                    Permission(
                        stationNo="500",
                        userDuz="10000000219",
                        contextName="OR CPRS GUI CHART",
                        rpcName="ORWPT LIST",
                    ),
                    Permission(
                        stationNo="500",
                        userDuz="10000000219",
                        contextName="OR CPRS GUI CHART",
                        rpcName="ORWPT ID INFO",
                    ),
                ],
                stations=[Station(stationNo="500", userDuz="10000000219")],
                configs=["ALLOW_VISTA_API_X_TOKEN"],
            ),
        ]

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
