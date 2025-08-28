"""DynamoDB Accelerator (DAX) cache implementation for AWS production use"""

import json
import logging
import time
from datetime import timedelta
from typing import Any

try:
    import boto3
    from botocore.exceptions import ClientError

    HAS_DAX = True
except ImportError:
    HAS_DAX = False

from .base import CacheBackend

logger = logging.getLogger(__name__)


class DAXBackend(CacheBackend):
    """DynamoDB Accelerator (DAX) cache backend for AWS production use"""

    def __init__(
        self,
        cluster_endpoint: str,
        region: str = "us-east-1",
        key_prefix: str = "mcp:",
        table_name: str = "vista_cache",
        connection_pool_kwargs: dict[str, Any] | None = None,
    ):
        """
        Initialize DAX backend.

        Args:
            cluster_endpoint: DAX cluster endpoint
            region: AWS region
            key_prefix: Prefix for all keys
            table_name: DynamoDB table name for cache storage
            connection_pool_kwargs: Additional connection pool arguments
        """
        if not HAS_DAX:
            raise ImportError(
                "DAX support not installed. Install with: pip install boto3"
            )

        self.cluster_endpoint = cluster_endpoint
        self.region = region
        self.key_prefix = key_prefix
        self.table_name = table_name
        self._client = None
        self._connection_pool_kwargs = connection_pool_kwargs or {}
        self._cluster_info: dict[str, Any] | None = None

    @property
    def default_ttl(self) -> timedelta:
        """Get default TTL for this cache backend."""
        return timedelta(hours=1)  # Default 1 hour TTL for DAX

    async def _get_cluster_info(self) -> dict[str, Any]:
        """Get DAX cluster information from AWS."""
        if self._cluster_info is None:
            try:
                # Extract cluster name from endpoint
                # Format: clustername.xxxxx.dax-clusters.amazonaws.com
                cluster_name = self.cluster_endpoint.split(".")[0]

                client = boto3.client("dax", region_name=self.region)
                response = client.describe_clusters(ClusterNames=[cluster_name])

                if response["Clusters"]:
                    self._cluster_info = response["Clusters"][0]
                    logger.info(f"Retrieved DAX cluster info: {cluster_name}")
                else:
                    logger.warning(f"DAX cluster not found: {cluster_name}")
                    self._cluster_info = {}

            except ClientError as e:
                logger.error(f"Failed to get DAX cluster info: {e}")
                self._cluster_info = {}
            except Exception as e:
                logger.error(f"Unexpected error getting cluster info: {e}")
                self._cluster_info = {}

        return self._cluster_info

    def _get_client(self):
        """Get or create DynamoDB client connection."""
        # Create new client if we don't have one
        if self._client is None:
            pool_kwargs = {
                "max_pool_size": 10,
                "max_retries": 3,
                "retry_delay": 0.1,
                **self._connection_pool_kwargs,
            }

            new_client = boto3.resource(
                "dynamodb",
                region_name=self.region,
                **pool_kwargs,
            )

            # Test connection by getting table reference
            try:
                table = new_client.Table(self.table_name)
                # Try to describe table to test connection
                table.load()
                logger.info(f"Connected to DynamoDB at {self.cluster_endpoint}")
                self._client = new_client
            except Exception as e:
                logger.error(f"Failed to connect to DynamoDB: {e}")
                raise

        # Return the client (either existing or newly created)
        return self._client

    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.key_prefix}{key}"

    def _make_dynamodb_item(
        self, key: str, value: Any, ttl: timedelta | None = None
    ) -> dict[str, Any]:
        """Create DynamoDB item for caching."""
        now = int(time.time())
        item = {
            "cache_key": key,
            "cache_value": json.dumps(value),
            "created_at": now,  # Current timestamp
        }

        if ttl:
            # Calculate expiry time
            expiry_time = now + int(ttl.total_seconds())
            item["expires_at"] = expiry_time

        return item

    def _is_expired(self, item: dict[str, Any]) -> bool:
        """Check if DynamoDB item is expired."""
        if "expires_at" not in item:
            return False

        current_time = int(time.time())
        return current_time > item["expires_at"]

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        try:
            client = self._get_client()
            prefixed_key = self._make_key(key)
            table = client.Table(self.table_name)

            # Get item from DynamoDB
            response = table.get_item(Key={"cache_key": prefixed_key})

            item = response.get("Item")
            if not item:
                return None

            # Check if expired
            if self._is_expired(item):
                # Remove expired item
                await self.delete(key)
                return None

            # Decode JSON value
            try:
                return json.loads(item["cache_value"])
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Failed to decode cached value for key {key}: {e}")
                # Remove corrupted data
                await self.delete(key)
                return None

        except Exception as e:
            logger.error(f"DAX get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: timedelta | None = None) -> bool:
        """Set value in cache."""
        try:
            client = self._get_client()
            prefixed_key = self._make_key(key)
            table = client.Table(self.table_name)

            # Create DynamoDB item
            item = self._make_dynamodb_item(prefixed_key, value, ttl)

            # Put item in DynamoDB
            table.put_item(Item=item)

            logger.debug(f"Cached key {key} with TTL {ttl}")
            return True

        except Exception as e:
            logger.error(f"DAX set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            client = self._get_client()
            prefixed_key = self._make_key(key)
            table = client.Table(self.table_name)

            # Delete item from DynamoDB
            response = table.delete_item(
                Key={"cache_key": prefixed_key}, ReturnValues="ALL_OLD"
            )

            # Check if item existed
            return "Attributes" in response

        except Exception as e:
            logger.error(f"DAX delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            client = self._get_client()
            prefixed_key = self._make_key(key)
            table = client.Table(self.table_name)

            # Check if item exists
            response = table.get_item(
                Key={"cache_key": prefixed_key},
                ProjectionExpression="cache_key, expires_at",
            )

            item = response.get("Item")
            if not item:
                return False

            # Check if expired
            if self._is_expired(item):
                # Remove expired item
                await self.delete(key)
                return False

            return True

        except Exception as e:
            logger.error(f"DAX exists error for key {key}: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all cached data by scanning and deleting items with our prefix."""
        try:
            client = self._get_client()
            table = client.Table(self.table_name)

            # Scan for all items with our prefix
            scan_kwargs = {
                "FilterExpression": "begins_with(cache_key, :prefix)",
                "ExpressionAttributeValues": {":prefix": self.key_prefix},
            }

            deleted_count = 0
            while True:
                response = table.scan(**scan_kwargs)

                # Delete items in batches
                for item in response.get("Items", []):
                    try:
                        table.delete_item(Key={"cache_key": item["cache_key"]})
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(
                            f"Failed to delete cache item {item['cache_key']}: {e}"
                        )

                # Continue scanning if there are more items
                if "LastEvaluatedKey" not in response:
                    break
                scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

            logger.info(
                f"Cleared {deleted_count} cache items with prefix {self.key_prefix}"
            )
            return True

        except Exception as e:
            logger.error(f"DAX clear error: {e}")
            return False

    async def close(self) -> None:
        """Close DAX connection."""
        # DynamoDB client doesn't have explicit close method
        # Just clear the reference
        self._client = None
        logger.debug("Closed DAX connection")

    async def ping(self) -> bool:
        """Check if DAX is available."""
        try:
            client = self._get_client()
            table = client.Table(self.table_name)
            # Try to describe table to test connection
            table.load()
            return True
        except Exception as e:
            logger.error(f"DAX ping failed: {e}")
            return False

    async def get_cluster_health(self) -> dict[str, Any]:
        """Get DAX cluster health information."""
        try:
            cluster_info = await self._get_cluster_info()

            if not cluster_info:
                return {"status": "unknown", "error": "No cluster info available"}

            # Check DAX connection
            dax_healthy = await self.ping()

            # Get cluster status
            cluster_status = cluster_info.get("Status", "unknown")

            # Get node information
            nodes = cluster_info.get("Nodes", [])
            node_statuses = [node.get("NodeStatus", "unknown") for node in nodes]

            return {
                "status": (
                    "healthy"
                    if dax_healthy and cluster_status == "available"
                    else "unhealthy"
                ),
                "cluster_status": cluster_status,
                "dax_healthy": dax_healthy,
                "node_count": len(nodes),
                "node_statuses": node_statuses,
                "endpoint": self.cluster_endpoint,
                "region": self.region,
                "table_name": self.table_name,
            }

        except Exception as e:
            logger.error(f"Failed to get cluster health: {e}")
            return {"status": "error", "error": str(e)}

    async def create_cache_table(self) -> bool:
        """Create the DynamoDB table for caching if it doesn't exist."""
        try:
            client = self._get_client()

            # Check if table exists
            try:
                table = client.Table(self.table_name)
                table.load()
                logger.info(f"Cache table {self.table_name} already exists")
                return True
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    # Table doesn't exist, create it
                    pass
                else:
                    raise

            # Create table
            table = client.create_table(
                TableName=self.table_name,
                KeySchema=[{"AttributeName": "cache_key", "KeyType": "HASH"}],
                AttributeDefinitions=[
                    {"AttributeName": "cache_key", "AttributeType": "S"}
                ],
                BillingMode="PAY_PER_REQUEST",
                TimeToLiveSpecification={
                    "Enabled": True,
                    "AttributeName": "expires_at",
                },
            )

            # Wait for table to be created
            table.meta.client.get_waiter("table_exists").wait(TableName=self.table_name)

            logger.info(f"Created cache table {self.table_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create cache table: {e}")
            return False
