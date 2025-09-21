# Outshine Syften Webhook (Ingest Service)

## Environment

Set one of the following:
- `SYFTEN_PUBSUB_TOPIC` with the full Pub/Sub topic path (`projects/<project>/topics/<topic>`)
- `GOOGLE_CLOUD_PROJECT` and `SYFTEN_PUBSUB_TOPIC_ID` to build the topic path at runtime

Values can be provided via shell exports or stored in `ingest/.env` which is loaded at startup. The application uses the default Google credentials available in the environment.

## Setup

1. Ensure [uv](https://github.com/astral-sh/uv) is installed locally or available in the container.
2. From the repository root run `uv venv` and `uv sync` to install dependencies.
3. Activate the environment with `source .venv/bin/activate` when working interactively.

## Local Run

```bash
uv run uvicorn ingest.main:app --host 0.0.0.0 --port 8000
```

Requests to `POST /syften-webhook` are validated and enqueued to Google Pub/Sub, logging both the raw payload and publish outcomes.
