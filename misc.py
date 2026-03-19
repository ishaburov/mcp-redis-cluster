from typing import Any, Dict, Union, List
import aiohttp

from redis.cluster import RedisCluster
from redis.exceptions import RedisError

from src.common.connection import RedisConnectionManager
from src.common.server import mcp
from src.common.config import MCP_DOCS_SEARCH_URL
from src.version import __version__


@mcp.tool()
async def delete(key: str) -> str:
    """Delete a Redis key.

    Args:
        key (str): The key to delete.

    Returns:
        str: Confirmation message or an error message.
    """
    try:
        r = RedisConnectionManager.get_connection()
        result = r.delete(key)
        return f"Successfully deleted {key}" if result else f"Key {key} not found"
    except RedisError as e:
        return f"Error deleting key {key}: {str(e)}"


@mcp.tool()
async def type(key: str) -> Dict[str, Any]:
    """Returns the string representation of the type of the value stored at key

    Args:
        key (str): The key to check.

    Returns:
        str: The type of key, or none when key doesn't exist
    """
    try:
        r = RedisConnectionManager.get_connection()
        key_type = r.type(key)
        info = {"key": key, "type": key_type, "ttl": r.ttl(key)}

        return info
    except RedisError as e:
        return {"error": str(e)}


@mcp.tool()
async def expire(name: str, expire_seconds: int) -> str:
    """Set an expiration time for a Redis key.

    Args:
        name: The Redis key.
        expire_seconds: Time in seconds after which the key should expire.

    Returns:
        A success message or an error message.
    """
    try:
        r = RedisConnectionManager.get_connection()
        success = r.expire(name, expire_seconds)
        return (
            f"Expiration set to {expire_seconds} seconds for '{name}'."
            if success
            else f"Key '{name}' does not exist."
        )
    except RedisError as e:
        return f"Error setting expiration for key '{name}': {str(e)}"


@mcp.tool()
async def rename(old_key: str, new_key: str) -> Dict[str, Any]:
    """
    Renames a Redis key from old_key to new_key.

    **Redis Cluster:** both keys must map to the **same hash slot** (same ``{...}`` tag);
    otherwise the tool returns an error without calling Redis.

    Args:
        old_key (str): The current name of the Redis key to rename.
        new_key (str): The new name to assign to the key.

    Returns:
        Dict[str, Any]: A dictionary containing the result of the operation.
            On success: {"status": "success", "message": "..."}
            On error: {"error": "..."}
    """
    try:
        r = RedisConnectionManager.get_connection()

        # Check if the old key exists
        if not r.exists(old_key):
            return {"error": f"Key '{old_key}' does not exist."}

        if isinstance(r, RedisCluster):
            slot_old = r.cluster_keyslot(old_key)
            slot_new = r.cluster_keyslot(new_key)
            if slot_old != slot_new:
                return {
                    "error": (
                        "Redis Cluster RENAME requires both keys in the same hash slot "
                        f"(slots {slot_old} and {slot_new}). Use the same {{...}} tag in names."
                    ),
                }

        # Rename the key
        r.rename(old_key, new_key)
        return {
            "status": "success",
            "message": f"Renamed key '{old_key}' to '{new_key}'",
        }

    except RedisError as e:
        return {"error": str(e)}


@mcp.tool()
async def scan_keys(
    pattern: str = "*", count: int = 100, cursor: int = 0
) -> Union[str, Dict[str, Any]]:
    """
    Scan keys in the Redis database using the SCAN command (non-blocking, production-safe).

    ⚠️  IMPORTANT: This returns PARTIAL results from one iteration. Use scan_all_keys()
    to get ALL matching keys, or call this function multiple times with the returned cursor
    until cursor becomes 0.

    **Redis Cluster:** redis-py returns a dict cursor per node; the MCP cannot expose that
    through a single integer. For cluster connections this tool uses ``scan_iter`` and
    returns at most ``count`` keys in one shot with ``scan_complete`` true. The ``cursor``
    argument is ignored in cluster mode. For a full listing, use ``scan_all_keys``.

    The SCAN command iterates through the keyspace in small chunks, making it safe to use
    on large databases without blocking other operations.

    Args:
        pattern: Pattern to match keys against (default is "*" for all keys).
                Common patterns: "user:*", "cache:*", "*:123", etc.
        count: Hint for the number of keys to return per iteration (default 100).
               Redis may return more or fewer keys than this hint.
        cursor: The cursor position to start scanning from (0 to start from beginning).
                To continue scanning, use the cursor value returned from previous call.

    Returns:
        A dictionary containing:
        - 'cursor': Next cursor position (0 means scan is complete)
        - 'keys': List of keys found in this iteration (PARTIAL RESULTS)
        - 'total_scanned': Number of keys returned in this batch
        - 'scan_complete': Boolean indicating if scan is finished
        Or an error message if something goes wrong.

    Example usage:
        First call: scan_keys("user:*") -> returns cursor=1234, keys=[...], scan_complete=False
        Next call: scan_keys("user:*", cursor=1234) -> continues from where it left off
        Final call: returns cursor=0, scan_complete=True when done
    """
    try:
        r = RedisConnectionManager.get_connection()
        if isinstance(r, RedisCluster):
            decoded_keys: List[str] = []
            for key in r.scan_iter(match=pattern, count=count):
                decoded_keys.append(
                    key.decode("utf-8") if isinstance(key, bytes) else key
                )
                if len(decoded_keys) >= count:
                    break
            return {
                "cursor": 0,
                "keys": decoded_keys,
                "total_scanned": len(decoded_keys),
                "scan_complete": True,
            }
        cursor, keys = r.scan(cursor=cursor, match=pattern, count=count)

        # Convert bytes to strings if needed
        decoded_keys = [
            key.decode("utf-8") if isinstance(key, bytes) else key for key in keys
        ]

        return {
            "cursor": cursor,
            "keys": decoded_keys,
            "total_scanned": len(decoded_keys),
            "scan_complete": cursor == 0,
        }
    except RedisError as e:
        return f"Error scanning keys with pattern '{pattern}': {str(e)}"


@mcp.tool()
async def scan_all_keys(
    pattern: str = "*", batch_size: int = 100
) -> Union[str, List[str]]:
    """
    Scan and return ALL keys matching a pattern using multiple SCAN iterations.

    This function automatically handles the SCAN cursor iteration to collect all matching keys.
    It's safer than KEYS * for large databases but will still collect all results in memory.

    **Redis Cluster:** uses ``scan_iter`` so all primaries are covered without passing a dict
    cursor back into ``SCAN`` (which redis-py rejects when encoded as a command argument).

    ⚠️  WARNING: With very large datasets (millions of keys), this may consume significant memory.
    For large-scale operations, consider using scan_keys() with manual iteration instead.

    Args:
        pattern: Pattern to match keys against (default is "*" for all keys).
        batch_size: Number of keys to scan per iteration (default 100).

    Returns:
        A list of all keys matching the pattern or an error message.
    """
    try:
        r = RedisConnectionManager.get_connection()
        if isinstance(r, RedisCluster):
            return [
                key.decode("utf-8") if isinstance(key, bytes) else key
                for key in r.scan_iter(match=pattern, count=batch_size)
            ]
        all_keys = []
        cursor = 0

        while True:
            cursor, keys = r.scan(cursor=cursor, match=pattern, count=batch_size)

            # Convert bytes to strings if needed and add to results
            decoded_keys = [
                key.decode("utf-8") if isinstance(key, bytes) else key for key in keys
            ]
            all_keys.extend(decoded_keys)

            # Break when scan is complete (cursor returns to 0)
            if cursor == 0:
                break

        return all_keys
    except RedisError as e:
        return f"Error scanning all keys with pattern '{pattern}': {str(e)}"


@mcp.tool()
async def search_redis_documents(
    question: str,
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """Search Redis documentation and knowledge base to learn about Redis concepts and use cases.

    This tool exposes updated and curated documentation, and must be invoked every time the user wants to learn more in areas including:

    **Common Use Cases:**
    - Session Management: User session storage and management
    - Caching: Application-level and database query caching
    - Rate Limiting: API throttling and request limiting
    - Leaderboards: Gaming and ranking systems
    - Semantic Search: AI-powered similarity search
    - Agentic Workflows: AI agent state and memory management
    - RAG (Retrieval-Augmented Generation): Vector storage for AI applications
    - Real-time Analytics: Counters, metrics, and time-series data
    - Message Queues: Task queues and job processing
    - Geospatial: Location-based queries and proximity search

    Args:
        question: The question about Redis concepts, data structures, features, or use cases

    Returns:
        Union[List[Dict[str, Any]], Dict[str, Any]]: A list of documentation results from the API, or a dict with an error message.
    """
    if not MCP_DOCS_SEARCH_URL:
        return {"error": "MCP_DOCS_SEARCH_URL environment variable is not configured"}

    if not question.strip():
        return {"error": "Question parameter cannot be empty"}

    try:
        headers = {
            "Accept": "application/json",
            "User-Agent": f"Redis-MCP-Server/{__version__}",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=MCP_DOCS_SEARCH_URL, params={"q": question}, headers=headers
            ) as response:
                # Try to parse JSON response
                try:
                    result = await response.json()
                    return result
                except aiohttp.ContentTypeError:
                    # If not JSON, return text content
                    text_content = await response.text()
                    return {"error": f"Non-JSON response: {text_content}"}

    except aiohttp.ClientError as e:
        return {"error": f"HTTP client error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error calling ConvAI API: {str(e)}"}
