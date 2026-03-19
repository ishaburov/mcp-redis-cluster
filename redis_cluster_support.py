"""Helpers for Redis MCP when connected via redis.cluster.RedisCluster."""

from redis.cluster import RedisCluster
from redis.exceptions import RedisError


def append_cluster_error_hint(client: object, exc: RedisError) -> str:
    """Add short context for common cluster-only or cluster+vanilla failures."""
    message: str = str(exc)
    if not isinstance(client, RedisCluster):
        return message
    lowered: str = message.lower()
    if "unknown command" in lowered:
        return (
            f"{message} Hint: plain open-source Redis Cluster usually has no "
            "RedisJSON or RediSearch (JSON.* / FT.* commands)."
        )
    if "crossslot" in lowered:
        return (
            f"{message} Hint: keys must share the same hash slot; use the same "
            "{{...}} hash tag in both key names."
        )
    return message
