# Outshine Syften Dispatcher

Consumes Syften items from the configured Google Pub/Sub subscription and forwards them to Slack.

## Environment

- `GOOGLE_CLOUD_PROJECT` – GCP project that owns the subscription (required when building the subscription path).
- `SYFTEN_PUBSUB_SUBSCRIPTION` – Full Pub/Sub subscription path (`projects/<project>/subscriptions/<subscription>`). Optional if the fields below are set.
- `SYFTEN_PUBSUB_SUBSCRIPTION_ID` – Subscription ID (used with `GOOGLE_CLOUD_PROJECT` when the full path is not provided).
- `SLACK_BOT_TOKEN` – Slack bot token with permission to post in the target channel.
- `SLACK_TEST_CHANNEL` – Channel ID or name to post messages into while testing (temporary until routing is added).
- `SLACK_SIGNING_SECRET` – Currently unused but stored for future interactive features.

Values can be stored in `.env` in this directory and are loaded automatically.

## Setup

```bash
cd dispatch
uv venv
uv sync
```

## Run

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8080
```

The service exposes `/healthz` for Cloud Run health checks and, on startup, opens a streaming pull to Pub/Sub to deliver each item to Slack. Messages that fail to decode or validate are acknowledged and dropped; Slack delivery failures are retried via Pub/Sub nack/backoff.
