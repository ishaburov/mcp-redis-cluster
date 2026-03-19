# Publishing to GitHub

The intended remote is `https://github.com/redis/mcp-redis-cluster.git`.

## Why push can fail

1. **Repository does not exist** — GitHub returns `Repository not found` until an **empty** repo is created (or you use `gh repo create` to create it).
2. **No credentials** — In this environment, `gh` needs **`GH_TOKEN`** (or run `gh auth login` in your own terminal).

## Publish with GitHub CLI (recommended)

From the repository root, after [creating a personal access token](https://github.com/settings/tokens) with `repo` scope (or fine-grained: contents read/write):

```bash
cd mcp-redis-cluster
export GH_TOKEN=ghp_your_token_here

# If the repo does NOT exist yet under YOUR user (replace YOUR_USER):
gh repo create YOUR_USER/mcp-redis-cluster --public --source=. --remote=origin --push

# If an empty repo already exists at redis/mcp-redis-cluster and you have org access:
git remote set-url origin https://github.com/redis/mcp-redis-cluster.git
git push -u origin main
```

Creating a repository **inside the `redis` organisation** requires an org owner/admin to create `mcp-redis-cluster` first, or to grant you permission to create repos there.

## Publish with SSH

```bash
git remote set-url origin git@github.com:redis/mcp-redis-cluster.git
git push -u origin main
```

(Ensure the empty repo exists and your SSH key is added to GitHub.)

## After a successful push

```bash
docker build -t redis-mcp-cluster:latest .
```
