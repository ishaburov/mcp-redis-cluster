# Publishing to GitHub

The remote `origin` is set to `https://github.com/redis/mcp-redis-cluster.git`.

`git push` fails until that repository **exists** and your account has **write access** to the `redis` organization.

## Option A — Repository under `redis` org (intended URL)

1. Ask a GitHub org admin for **redis** to create a new **public** repository named `mcp-redis-cluster` (empty, no README).
2. Grant your user **push** access (or merge via pull request from a fork).
3. From this folder:

```bash
cd mcp-redis-cluster
git push -u origin main
```

## Option B — Your fork first

1. Create `https://github.com/<you>/mcp-redis-cluster` (empty).
2. `git remote set-url origin https://github.com/<you>/mcp-redis-cluster.git`
3. `git push -u origin main`
4. Open a pull request to `redis/mcp-redis-cluster` when the upstream repo exists.

## Verify

After push, the default build command is:

```bash
docker build -t redis-mcp-cluster:latest .
```
