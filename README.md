# Outshine Syften Webhook

This repository houses multiple services that integrate with the Syften webhook pipeline. The current implementation includes the ingest service (under `ingest/`) that accepts webhook payloads and publishes validated items to Google Pub/Sub. Additional services, such as the dispatcher, can live alongside it (for example, under `dispatch/`).

## Repository Layout

- `ingest/` – FastAPI webhook for receiving Syften items and enqueueing them to Pub/Sub. Contains its own Dockerfile, service-specific README, and configuration assets.
- `dispatch/` – Placeholder directory for the upcoming Slack dispatcher service.

Each service owns its dependencies and container configuration inside its directory so they can be built and deployed independently.

## Working on the Ingest Service

```bash
cd ingest
uv venv
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

Build the ingest container (local example):

```bash
cd ingest
docker build -t ingest-service .
```

Add new services in dedicated subdirectories with their own dependency manifests and Dockerfiles.
