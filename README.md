# mcp-redis-cluster

Docker image build that extends **[redis/mcp-redis](https://github.com/redis/mcp-redis)** with **Redis Cluster**–safe behaviour. Use it when `REDIS_CLUSTER_MODE=true` and redis-py returns a **dict** cursor from `SCAN` (which breaks the upstream `scan_keys` / `scan_all_keys` tools).

## Fixes vs upstream `mcp-redis`

| Tool / area | Cluster behaviour |
|-------------|-------------------|
| `scan_keys`, `scan_all_keys` | Uses `scan_iter` on `RedisCluster` (avoids `DataError: Invalid input of type: 'dict'`). |
| `dbsize` | Sums `DBSIZE` on all **primary** nodes. |
| `info` | Returns `{ cluster_mode, primary_count, primaries: { node → INFO } }`. |
| `client_list` | Merges `CLIENT LIST` from every primary; each row has `redis_node`. |
| `rename` | Pre-checks `cluster_keyslot`; rejects different slots with a clear message. |
| Pub/sub tools | Docstrings clarify MCP limitations (no message streaming to the agent). |
| `json_*`, RediSearch / vector tools | Enriched errors on `unknown command` (plain cluster often has no RedisJSON/RediSearch). |

## Build

```bash
git clone https://github.com/redis/mcp-redis-cluster.git
cd mcp-redis-cluster
docker build -t redis-mcp-cluster:latest .
```

Override the upstream pin if needed:

```bash
docker build --build-arg MCP_REDIS_SHA=<commit_sha> -t redis-mcp-cluster:latest .
```

## Run (example: Docker Compose network)

```bash
docker run -i --rm \
  --network your_redis_network \
  -e REDIS_HOST=redis-cluster \
  -e REDIS_PORT=7000 \
  -e REDIS_CLUSTER_MODE=true \
  redis-mcp-cluster:latest
```

## Cursor / MCP client

Point your MCP server config at the image you built, for example:

```json
{
  "mcpServers": {
    "redis": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "--network", "your_network",
        "-e", "REDIS_HOST=redis-cluster",
        "-e", "REDIS_PORT=7000",
        "-e", "REDIS_CLUSTER_MODE=true",
        "redis-mcp-cluster:latest"
      ]
    }
  }
}
```

## Upstream alignment

- Base: `https://github.com/redis/mcp-redis` at commit `MCP_REDIS_SHA` (see `Dockerfile`).
- Prefer **merging these changes into `redis/mcp-redis`** long term so a separate image is unnecessary.

## License

MIT — see [LICENSE](./LICENSE). Upstream is copyright Redis, Inc.
