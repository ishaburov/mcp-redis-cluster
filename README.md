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
| Connection | **`REDIS_CLUSTER_NODES`**: comma-separated `host:port` list → `RedisCluster(startup_nodes=...)` so discovery is not tied to a single endpoint. If unset, **`REDIS_HOST`** + **`REDIS_PORT`** are used as one startup node (upstream behaviour). |

## Configuration (cluster)

| Variable | Meaning |
|----------|---------|
| `REDIS_CLUSTER_MODE` | `true` / `1` / `t` to use `RedisCluster`. |
| `REDIS_CLUSTER_NODES` | Optional. Example: `redis-cluster:7000,redis-cluster:7001,...` — **startup nodes** for the client (redis-py discovers the full topology from them). |
| `REDIS_HOST` / `REDIS_PORT` | Used when `REDIS_CLUSTER_NODES` is empty; default port is also used for host-only entries in `REDIS_CLUSTER_NODES` (`hostname` without `:port`). |

## Prebuilt image (GHCR)

After each push to `main`, GitHub Actions builds and pushes:

`ghcr.io/ishaburov/mcp-redis-cluster:latest`

Pull (package must be **public** or you must `docker login ghcr.io`):

```bash
docker pull ghcr.io/ishaburov/mcp-redis-cluster:latest
```

Use that image in MCP / Compose instead of a local build. Tag `v1.2.3` also publishes semver tags.

## Build locally

```bash
git clone https://github.com/ishaburov/mcp-redis-cluster.git
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
  -e REDIS_CLUSTER_MODE=true \
  -e REDIS_CLUSTER_NODES=redis-cluster:7000,redis-cluster:7001,redis-cluster:7002,redis-cluster:7003,redis-cluster:7004,redis-cluster:7005 \
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
        "-e", "REDIS_CLUSTER_MODE=true",
        "-e", "REDIS_CLUSTER_NODES=redis-cluster:7000,redis-cluster:7001,redis-cluster:7002,redis-cluster:7003,redis-cluster:7004,redis-cluster:7005",
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
