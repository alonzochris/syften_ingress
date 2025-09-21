import asyncio
import json
import logging
import os
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from google.cloud import pubsub_v1
from pydantic import BaseModel, ValidationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("syften_webhook")

load_dotenv()

app = FastAPI()


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


topic_path = os.environ.get("SYFTEN_PUBSUB_TOPIC")
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
topic_id = os.environ.get("SYFTEN_PUBSUB_TOPIC_ID")

publisher_client = pubsub_v1.PublisherClient()

if topic_path:
    topic_path = topic_path
elif project_id and topic_id:
    topic_path = publisher_client.topic_path(project_id, topic_id)
else:
    raise RuntimeError("SYFTEN_PUBSUB_TOPIC or both GOOGLE_CLOUD_PROJECT and SYFTEN_PUBSUB_TOPIC_ID must be set")


def publish_message(data: bytes, attributes: dict):
    future = publisher_client.publish(topic_path, data, **attributes)
    return future.result()


async def enqueue_items(items: List[Item]):
    loop = asyncio.get_running_loop()
    tasks = []
    for item in items:
        payload = json.dumps(item.model_dump(mode="json")).encode("utf-8")
        attributes = {}
        if item.filter:
            attributes["filter"] = item.filter
        if item.backend:
            attributes["backend"] = item.backend
        if item.backend_sub:
            attributes["backend_sub"] = item.backend_sub
        tasks.append(loop.run_in_executor(None, publish_message, payload, attributes))
    if tasks:
        await asyncio.gather(*tasks)


@app.post("/syften-webhook")
async def items_handler(request: Request):
    body = await request.body()
    logger.info("Raw payload: %s", body.decode("utf-8", "replace"))
    if not body:
        raise HTTPException(status_code=400, detail="No body provided")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    if not isinstance(payload, list):
        raise HTTPException(status_code=400, detail="Payload must be a list of items")
    try:
        items = [Item.model_validate(item) for item in payload]
    except ValidationError as exc:
        logger.warning("Validation error: %s", exc.errors())
        raise HTTPException(status_code=422, detail=exc.errors())
    if not items:
        raise HTTPException(status_code=400, detail="No items provided")
    try:
        await enqueue_items(items)
    except Exception:
        logger.exception("Failed to publish items to Pub/Sub")
        raise HTTPException(status_code=500, detail="Failed to enqueue items")
    count = len(items)
    logger.info("Received %d items", count)
    return {"received": count}
