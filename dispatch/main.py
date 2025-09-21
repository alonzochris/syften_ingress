import json
import logging
import os
from concurrent.futures import CancelledError, ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber.futures import StreamingPullFuture
from pydantic import BaseModel, ValidationError
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("syften_dispatch")


class Item(BaseModel):
    backend: str
    backend_sub: Optional[str] = None
    type: str
    icon_url: str
    timestamp: datetime
    item_url: str
    author: str
    parent_author: Optional[str] = None
    text: str
    title: str
    title_type: int
    meta: Optional[dict] = None
    lang: Optional[str] = None
    filter: str

    class Config:
        extra = "allow"


slack_token = os.environ.get("SLACK_BOT_TOKEN")
slack_test_channel = os.environ.get("SLACK_TEST_CHANNEL") or os.environ.get("SLACK_CHANNEL")
if not slack_token:
    raise RuntimeError("SLACK_BOT_TOKEN must be set")
if not slack_test_channel:
    raise RuntimeError("SLACK_TEST_CHANNEL must be set")

slack_client = WebClient(token=slack_token)

subscriber_client = pubsub_v1.SubscriberClient()
subscription_path = os.environ.get("SYFTEN_PUBSUB_SUBSCRIPTION")
if not subscription_path:
    subscription_id = os.environ.get("SYFTEN_PUBSUB_SUBSCRIPTION_ID")
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if subscription_id and subscription_id.startswith("projects/"):
        subscription_path = subscription_id
    elif project_id and subscription_id:
        subscription_path = subscriber_client.subscription_path(project_id, subscription_id)
    else:
        raise RuntimeError(
            "Provide SYFTEN_PUBSUB_SUBSCRIPTION with the full path or set GOOGLE_CLOUD_PROJECT and "
            "SYFTEN_PUBSUB_SUBSCRIPTION_ID"
        )


executor = ThreadPoolExecutor(max_workers=1)
streaming_pull_future: Optional[StreamingPullFuture] = None


def build_slack_message(item: Item) -> tuple[str, List[dict]]:
    title = item.title or "New item"
    fallback_text = f"{title} – {item.item_url}" if item.item_url else title

    blocks: List[dict] = []

    header_text = title
    blocks.append({
        "type": "header",
        "text": {"type": "plain_text", "text": header_text, "emoji": False},
    })

    section_lines = []
    if item.text:
        section_lines.append(item.text)
    if not section_lines:
        section_lines.append("No description provided")

    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": "\n".join(section_lines)},
    })

    if item.item_url:
        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Source", "emoji": False},
                        "url": item.item_url,
                        "style": "primary",
                    }
                ],
            }
        )

    blocks.append({"type": "divider"})

    context_elements = []
    if item.backend:
        backend_label = item.backend_sub or item.backend
        context_elements.append({"type": "mrkdwn", "text": f"*Source:* {backend_label}"})
    if item.timestamp:
        context_elements.append(
            {
                "type": "mrkdwn",
                "text": f"*Published:* {item.timestamp.strftime('%Y-%m-%d')}",
            }
        )

    if context_elements:
        blocks.append({"type": "context", "elements": context_elements})

    return fallback_text, blocks


def handle_message(message: pubsub_v1.subscriber.message.Message) -> None:
    try:
        payload = json.loads(message.data.decode("utf-8"))
        item = Item.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.warning("Dropping invalid message: %s", exc)
        message.ack()
        return

    fallback_text, blocks = build_slack_message(item)
    try:
        logger.info("Dispatching item payload: %s", item.model_dump(mode="json"))
        slack_client.chat_postMessage(
            channel=slack_test_channel,
            text=fallback_text,
            blocks=blocks,
        )
        logger.info("Dispatched item %s", item.item_url)
        message.ack()
    except SlackApiError as exc:
        logger.error("Slack API error: %s", exc.response.get("error"))
        message.nack()
    except Exception:
        logger.exception("Unexpected error while dispatching to Slack")
        message.nack()

def start_streaming_pull() -> None:
    global streaming_pull_future
    streaming_pull_future = subscriber_client.subscribe(subscription_path, callback=handle_message)
    logger.info("Listening for messages on %s", subscription_path)
    try:
        streaming_pull_future.result()
    except CancelledError:
        logger.info("Streaming pull for %s cancelled", subscription_path)
    except Exception:
        logger.exception("Streaming pull for %s terminated unexpectedly", subscription_path)


@asynccontextmanager
async def lifespan(_: FastAPI):
    executor.submit(start_streaming_pull)
    try:
        yield
    finally:
        global streaming_pull_future
        if streaming_pull_future:
            streaming_pull_future.cancel()
            streaming_pull_future = None
        subscriber_client.close()
        executor.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)


@app.get("/healthz")
async def healthcheck() -> dict:
    return {"status": "ok"}
