from typing import TYPE_CHECKING
from apis.pubsub_models import Outage

if TYPE_CHECKING:
    from redis import Redis
    from app.scraper import Record


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

        self.redis.publish(self.channel, msg)
