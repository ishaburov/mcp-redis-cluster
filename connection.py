import logging
from typing import Any, Dict, List, Optional, Type, Union

import redis
from redis import Redis
from redis.cluster import ClusterNode, RedisCluster

from src.common.config import REDIS_CFG, is_entraid_auth_enabled
from src.common.entraid_auth import (
    create_credential_provider,
    EntraIDAuthenticationError,
)
from src.version import __version__

_logger = logging.getLogger(__name__)


class RedisConnectionManager:
    _instance: Optional[Redis] = None

    @classmethod
    def get_connection(cls, decode_responses=True) -> Redis:
        if cls._instance is None:
            try:
                credential_provider = None
                if is_entraid_auth_enabled():
                    try:
                        credential_provider = create_credential_provider()
                    except EntraIDAuthenticationError as e:
                        _logger.error(
                            "Failed to create Entra ID credential provider: %s", e
                        )
                        raise

                if REDIS_CFG["cluster_mode"]:
                    redis_class: Type[Union[Redis, RedisCluster]] = (
                        redis.cluster.RedisCluster
                    )
                    connection_params: Dict[str, Any] = {
                        "username": REDIS_CFG["username"],
                        "password": REDIS_CFG["password"],
                        "ssl": REDIS_CFG["ssl"],
                        "ssl_ca_path": REDIS_CFG["ssl_ca_path"],
                        "ssl_keyfile": REDIS_CFG["ssl_keyfile"],
                        "ssl_certfile": REDIS_CFG["ssl_certfile"],
                        "ssl_cert_reqs": REDIS_CFG["ssl_cert_reqs"],
                        "ssl_ca_certs": REDIS_CFG["ssl_ca_certs"],
                        "decode_responses": decode_responses,
                        "lib_name": f"redis-py(mcp-server_v{__version__})",
                        "max_connections_per_node": 10,
                    }
                    startup_nodes: Optional[List[Dict[str, Any]]] = REDIS_CFG.get(
                        "cluster_startup_nodes"
                    )
                    if startup_nodes:
                        connection_params["startup_nodes"] = [
                            ClusterNode(str(n["host"]), int(n["port"]))
                            for n in startup_nodes
                        ]
                    else:
                        connection_params["host"] = REDIS_CFG["host"]
                        connection_params["port"] = REDIS_CFG["port"]
                    if credential_provider:
                        connection_params["credential_provider"] = credential_provider
                else:
                    redis_class = redis.Redis
                    connection_params = {
                        "host": REDIS_CFG["host"],
                        "port": REDIS_CFG["port"],
                        "db": REDIS_CFG["db"],
                        "username": REDIS_CFG["username"],
                        "password": REDIS_CFG["password"],
                        "ssl": REDIS_CFG["ssl"],
                        "ssl_ca_path": REDIS_CFG["ssl_ca_path"],
                        "ssl_keyfile": REDIS_CFG["ssl_keyfile"],
                        "ssl_certfile": REDIS_CFG["ssl_certfile"],
                        "ssl_cert_reqs": REDIS_CFG["ssl_cert_reqs"],
                        "ssl_ca_certs": REDIS_CFG["ssl_ca_certs"],
                        "decode_responses": decode_responses,
                        "lib_name": f"redis-py(mcp-server_v{__version__})",
                        "max_connections": 10,
                    }
                    if credential_provider:
                        connection_params["credential_provider"] = credential_provider

                cls._instance = redis_class(**connection_params)

            except redis.exceptions.ConnectionError:
                _logger.error("Failed to connect to Redis server")
                raise
            except redis.exceptions.AuthenticationError:
                _logger.error("Authentication failed")
                raise
            except redis.exceptions.TimeoutError:
                _logger.error("Connection timed out")
                raise
            except redis.exceptions.ResponseError as e:
                _logger.error("Response error: %s", e)
                raise
            except redis.exceptions.RedisError as e:
                _logger.error("Redis error: %s", e)
                raise
            except redis.exceptions.ClusterError as e:
                _logger.error("Redis Cluster error: %s", e)
                raise
            except Exception as e:
                _logger.error("Unexpected error: %s", e)
                raise

        return cls._instance
