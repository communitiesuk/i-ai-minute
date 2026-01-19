# Viewer (Docker)

From the repo root, eval runs are stored at `evals/runs`.

## Build

Run from inside the `viewer/` folder:

```bash
docker build -t i-ai-minute-viewer -f Dockerfile ..
```

## Run

Note: bind mounts (e.g. `../evals/runs`) are configured at `docker run` time; a `Dockerfile` cannot hardcode a host path.

```bash
docker run --rm \
  -p 8080:8080 \
  -v "$(pwd)/../evals/runs:/data/runs" \
  i-ai-minute-viewer
```

Open:

- <http://localhost:8080>
