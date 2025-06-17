import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from app.publisher import ParsedRecord
from app.scraper import Record

if TYPE_CHECKING:
    from app.parser import OutageDetailsParser, OrganizationParser
    from app.publisher import Publisher
    from app.scraper import Scraper
    from app.storage import Storage

logger = logging.getLogger(__name__)


class PeriodicTask:
    def __init__(
        self,
        scraper: "Scraper",
        storage: "Storage",
        publisher: "Publisher",
        outage_parser: "OutageDetailsParser",
        organization_parser: "OrganizationParser",
        interval: int,
    ):
        self.scraper = scraper
        self.storage = storage
        self.publisher = publisher
        self.outage_parser = outage_parser
        self.organization_parser = organization_parser

        self.interval = interval

        self.is_running = False

    async def start(self):
        self.is_running = True
        while self.is_running:
            await self.run()
            await asyncio.sleep(self.interval)

    async def stop(self):
        self.is_running = False

    async def run(self):
        logger.info("Running periodic task...")

        try:
            records = await self.scraper.run()
            logger.info("Got %d records", len(records))

            records = [
                r
                for r in [
                    await self._fill_details(record)
                    for record in records
                    if not all(d < datetime.now() for d in record.dates)
                ]
                if r is not None
            ]
            logger.info("After date filter %d records", len(records))

            changes = await self.storage.diff(records)
            logger.info("Total changed %d records", len(changes))
            if not changes:
                return

            logger.info("Changes:")
            for record in changes:
                logger.info(record)

            for record in changes:
                try:
                    await self.publisher.publish(record)
                except Exception as e:
                    logger.error("Failed to publish outage: %s", e, exc_info=True)
                    records.remove(record)

            await self.storage.commit(records)
        except Exception as e:
            logger.error("Failed to commit records: %s", e, exc_info=True)

    async def _fill_details(self, record: "Record") -> ParsedRecord | None:
        try:
            organization = self.organization_parser.parse(record.organization)
            if not organization:
                raise ValueError("Failed to parse organization")

            details = await self.outage_parser.parse(record.address)
            if not details:
                raise ValueError("Failed to parse details")

            return ParsedRecord(
                area=record.area,
                organization=organization,
                details=details,
                dates=record.dates,
            )
        except Exception:
            logger.warning("Failed to parse record: %s", str(record), exc_info=True)
            return None
