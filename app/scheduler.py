import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.parser import OutageDetailsParser
    from app.publisher import Publisher
    from app.scraper import Scraper, Record
    from app.storage import Storage

logger = logging.getLogger(__name__)


class PeriodicTask:
    def __init__(
        self,
        scraper: "Scraper",
        storage: "Storage",
        publisher: "Publisher",
        outage_parser: "OutageDetailsParser",
        interval: int,
    ):
        self.scraper = scraper
        self.storage = storage
        self.publisher = publisher
        self.outage_parser = outage_parser

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
                await self._fill_details(record)
                for record in records
                if not all(d < datetime.now() for d in record.dates)
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

    async def _fill_details(self, record: "Record"):
        try:
            details = await self.outage_parser.parse(record.address)
            if details is not None:
                record.address = str(details)
            # Optionally, add an else case if you want to modify behavior when parsing fails
        except Exception as e:
            logger.warning("Failed to parse address details: %s", e, exc_info=True)

        # Continue with original address
        return record
