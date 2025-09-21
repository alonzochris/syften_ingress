# Outshine Syften Webhook

This repository houses multiple services that integrate with the Syften webhook pipeline. The current implementation includes the ingest service (under `ingest/`) that accepts webhook payloads and publishes validated items to Google Pub/Sub. Additional services, such as the dispatcher, can live alongside it (for example, under `dispatch/`).

## Repository Layout

- `ingest/` – FastAPI webhook for receiving Syften items and enqueueing them to Pub/Sub. Contains its own Dockerfile, service-specific README, and configuration assets.
- `dispatch/` – Placeholder directory for the upcoming Slack dispatcher service.
- `pyproject.toml`, `uv.lock` – Shared dependency definitions managed through `uv` for all services.

## Common Workflow

Install dependencies with uv:

```bash
uv venv
uv sync
```

Run individual services from the repository root, e.g. the ingest service:

```bash
uv run uvicorn ingest.main:app --host 0.0.0.0 --port 8000
```

Build service containers with their local Dockerfiles, for example:

```bash
docker build -f ingest/Dockerfile .
```

Add new services in dedicated subdirectories and reuse the shared tooling as needed.
