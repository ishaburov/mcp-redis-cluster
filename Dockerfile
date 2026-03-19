# Patched redis/mcp-redis for Redis Cluster: SCAN (scan_iter), DBSIZE/INFO/CLIENT LIST
# aggregation on primaries, RENAME slot check, module error hints, pub/sub docs.
FROM python:3.14-slim

LABEL io.modelcontextprotocol.server.name="io.github.redis/mcp-redis"
LABEL org.opencontainers.image.description="Redis MCP + Redis Cluster compatibility (overlay)"
LABEL org.opencontainers.image.source="https://github.com/redis/mcp-redis-cluster"

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade uv

WORKDIR /app

# Pin to the same commit as the previously built local mcp/redis image (reproducible).
ARG MCP_REDIS_SHA=05a581bc87827d375b1215c5c4495393181ce1a8
RUN git clone https://github.com/redis/mcp-redis.git /tmp/mcp-redis \
    && cd /tmp/mcp-redis \
    && git checkout "${MCP_REDIS_SHA}" \
    && cp -a /tmp/mcp-redis/. /app/ \
    && rm -rf /tmp/mcp-redis

COPY redis_cluster_support.py /app/src/common/redis_cluster_support.py
COPY misc.py /app/src/tools/misc.py
COPY server_management.py /app/src/tools/server_management.py
COPY pub_sub.py /app/src/tools/pub_sub.py
COPY json.py /app/src/tools/json.py
COPY redis_query_engine.py /app/src/tools/redis_query_engine.py

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

CMD ["uv", "run", "python", "src/main.py"]
