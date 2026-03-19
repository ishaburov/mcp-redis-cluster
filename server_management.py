from typing import Any, Dict, List, Union

from redis.cluster import RedisCluster
from redis.exceptions import RedisError

from src.common.connection import RedisConnectionManager
from src.common.server import mcp


@mcp.tool()
async def dbsize() -> Union[int, str]:
    """Get the number of keys in the database.

    **Redis Cluster:** sums ``DBSIZE`` on each **primary** master (each key lives on one
    primary; replicas are not added, so the total matches cluster-wide key count).
    """
    try:
        r = RedisConnectionManager.get_connection()
        if isinstance(r, RedisCluster):
            total: int = 0
            for node in r.get_primaries():
                count = r.execute_command("DBSIZE", target_nodes=node)
                total += int(count)
            return total
        return r.dbsize()
    except RedisError as e:
        return f"Error getting database size: {str(e)}"


@mcp.tool()
async def info(section: str = "default") -> Union[Dict[str, Any], str]:
    """Get Redis server information and statistics.

    **Redis Cluster:** returns ``cluster_mode``, ``primary_count``, and ``primaries``
    (map ``node_name`` -> parsed INFO for that primary). Single-node Redis returns a
    flat INFO dict as before.
    """
    try:
        r = RedisConnectionManager.get_connection()
        if isinstance(r, RedisCluster):
            primaries: Dict[str, Dict[str, Any]] = {}
            for node in r.get_primaries():
                if section == "default":
                    inf = r.info(target_nodes=node)
                else:
                    inf = r.info(section, target_nodes=node)
                primaries[node.name] = inf
            return {
                "cluster_mode": True,
                "primary_count": len(primaries),
                "primaries": primaries,
            }
        return r.info(section)
    except RedisError as e:
        return f"Error retrieving Redis info: {str(e)}"


@mcp.tool()
async def client_list() -> Union[List[Dict[str, Any]], str]:
    """List connected clients.

    **Redis Cluster:** runs ``CLIENT LIST`` on every primary and merges results; each
    row includes ``redis_node`` (endpoint name of that primary).
    """
    try:
        r = RedisConnectionManager.get_connection()
        if isinstance(r, RedisCluster):
            aggregated: List[Dict[str, Any]] = []
            for node in r.get_primaries():
                clients = r.client_list(target_nodes=node)
                for row in clients:
                    if isinstance(row, dict):
                        merged: Dict[str, Any] = {**row, "redis_node": node.name}
                    else:
                        merged = {"redis_node": node.name, "raw": row}
                    aggregated.append(merged)
            return aggregated
        return r.client_list()
    except RedisError as e:
        return f"Error retrieving client list: {str(e)}"
