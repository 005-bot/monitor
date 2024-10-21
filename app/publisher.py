import logging
from typing import TYPE_CHECKING
from apis.pubsub_models import Outage

if TYPE_CHECKING:
    from redis import Redis
    from app.scraper import Record

logger = logging.getLogger(__name__)


class Publisher:
    def __init__(self, redis: "Redis", prefix: str):
        self.channel = f"{prefix}:outages"
        self.redis = redis

    async def publish(self, outage: "Record"):
        msg = Outage(
            area=outage.area,
            organization=outage.organization,
            address=outage.address,
            dates=outage.dates,
        ).to_json()

        try:
            self.redis.publish(self.channel, msg)
            logger.info(f"Published outage: {msg}")
        except Exception as e:
            logger.error(f"Failed to publish outage: {e}", exc_info=True)
