# mcp-redis-cluster

Docker image extending **[redis/mcp-redis](https://github.com/redis/mcp-redis)** with **Redis Cluster**–safe MCP tools (fixes `SCAN` dict-cursor issues and related cluster semantics).

## Recommended: use the published image (GHCR)

**Default image to run:**

`ghcr.io/ishaburov/mcp-redis-cluster:latest`

Built automatically on every push to `main` (see [`.github/workflows/docker-publish.yml`](.github/workflows/docker-publish.yml)).

```bash
docker pull ghcr.io/ishaburov/mcp-redis-cluster:latest
```

If the package is **private**, log in first:

```bash
echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

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
| Connection | **`REDIS_CLUSTER_NODES`**: comma-separated `host:port` → multiple **startup nodes**. If unset, **`REDIS_HOST`** + **`REDIS_PORT`**. |

## Configuration (cluster)

| Variable | Meaning |
|----------|---------|
| `REDIS_CLUSTER_MODE` | `true` / `1` / `t` to use `RedisCluster`. |
| `REDIS_CLUSTER_NODES` | Optional. Example: `redis-cluster:7000,redis-cluster:7001,...` — **startup nodes** (redis-py discovers the full topology). |
| `REDIS_HOST` / `REDIS_PORT` | Used when `REDIS_CLUSTER_NODES` is empty; default port for host-only entries in `REDIS_CLUSTER_NODES`. |

## Cursor / MCP client (copy-paste)

Use the **GHCR** image name as the last argument to `docker run`:

```json
{
  "mcpServers": {
    "redis": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--network",
        "your_docker_network",
        "-e",
        "REDIS_CLUSTER_MODE=true",
        "-e",
        "REDIS_CLUSTER_NODES=redis-cluster:7000,redis-cluster:7001,redis-cluster:7002,redis-cluster:7003,redis-cluster:7004,redis-cluster:7005",
        "ghcr.io/ishaburov/mcp-redis-cluster:latest"
      ]
    }
  }
}
```

Replace `your_docker_network` with the network your Redis Cluster containers use (e.g. Compose project network).

## Run manually (same image)

```bash
docker run -i --rm \
  --network your_docker_network \
  -e REDIS_CLUSTER_MODE=true \
  -e REDIS_CLUSTER_NODES=redis-cluster:7000,redis-cluster:7001,redis-cluster:7002,redis-cluster:7003,redis-cluster:7004,redis-cluster:7005 \
  ghcr.io/ishaburov/mcp-redis-cluster:latest
```

## Build locally (optional)

Only if you need a custom `MCP_REDIS_SHA` or local patches:

```bash
git clone https://github.com/ishaburov/mcp-redis-cluster.git
cd mcp-redis-cluster
docker build -t redis-mcp-cluster:local .
```

```bash
docker build --build-arg MCP_REDIS_SHA=<commit_sha> -t redis-mcp-cluster:local .
```

Releases tagged `v*` on GitHub also produce semver tags on GHCR (e.g. `ghcr.io/ishaburov/mcp-redis-cluster:1.0.0`).

## Upstream alignment

- Base: `https://github.com/redis/mcp-redis` at commit `MCP_REDIS_SHA` (see `Dockerfile`).
- Long term, merging into **`redis/mcp-redis`** would avoid a separate image.

## License

MIT — see [LICENSE](./LICENSE). Upstream is copyright Redis, Inc.
