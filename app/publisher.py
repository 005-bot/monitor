import logging
from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING

from apis.pubsub_models import Outage
from pydantic import BaseModel

from app.parser import format_dates
from app.parser.organization import OrganizationInfo
from app.parser.outage_details import OutageDetails

if TYPE_CHECKING:
    from redis import Redis

    from app.scraper import Record

logger = logging.getLogger(__name__)


class ParsedRecord(BaseModel):
    area: str
    organization: OrganizationInfo
    details: OutageDetails
    dates: list[datetime]

    @cached_property
    def address(self):
        return "\n".join([str(s) for s in self.details.streets])


class Publisher:
    def __init__(self, redis: "Redis", prefix: str):
        self.channel = f"{prefix}:outages"
        self.redis = redis

    async def publish(self, outage: ParsedRecord):
        msg = Outage(
            area=outage.area,
            organization=str(outage.organization),
            address=str(outage.details),
            dates=format_dates(outage.dates),
        ).to_json()

        try:
            self.redis.publish(self.channel, msg)
            logger.info("Published outage: %s", msg)
        except Exception:
            logger.exception("Failed to publish outage")
