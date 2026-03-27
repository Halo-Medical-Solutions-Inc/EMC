import json
from typing import Any, Dict

from app.database.redis_client import get_redis

CHANNEL_NAME = "emc_events"


async def publish_event(event_type: str, data: Dict[str, Any]) -> None:
    redis = await get_redis()
    message = json.dumps({"type": event_type, "data": data})
    await redis.publish(CHANNEL_NAME, message)
