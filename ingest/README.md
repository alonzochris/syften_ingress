# Outshine Syften Webhook (Ingest Service)

## Environment

Set one of the following:
- `SYFTEN_PUBSUB_TOPIC` with the full Pub/Sub topic path (`projects/<project>/topics/<topic>`)
- `GOOGLE_CLOUD_PROJECT` and `SYFTEN_PUBSUB_TOPIC_ID` to build the topic path at runtime

Values can be provided via shell exports or stored in `.env` (within this directory) which is loaded at startup. The application uses the default Google credentials available in the environment.

## Setup

```bash
cd ingest
uv venv
uv sync
source .venv/bin/activate  # optional for interactive work
```

## Local Run

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

Requests to `POST /syften-webhook` are validated and enqueued to Google Pub/Sub, logging both the raw payload and publish outcomes.

## Container Build

```bash
docker build -t ingest-service .
```
