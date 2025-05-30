import asyncio
import logging
import signal
import sys

import redis
from address_parser import AddressParser

from app.config import config
from app.parser.outage_details import OutageDetailsParser
from app.publisher import Publisher
from app.scheduler import PeriodicTask
from app.scraper import Scraper
from app.storage import Storage

logger = logging.getLogger(__name__)


async def main():
    loop = asyncio.get_running_loop()
    logger.info("Starting...")
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(loop)))

    r = redis.from_url(config.redis.url, decode_responses=True)
    logger.info("Created Redis instance")

    storage = Storage(r, config.storage.prefix, config.storage.ttl)
    await storage.migrate()
    logger.info("Created Storage instance")

    publisher = Publisher(r, config.publisher.prefix)

    async with Scraper(
        config.scraper.url, storage=storage
    ) as scraper, AddressParser() as address_parser:
        task = PeriodicTask(
            scraper=scraper,
            storage=storage,
            publisher=publisher,
            outage_parser=OutageDetailsParser(address_parser),
            interval=config.scraper.interval,
        )
        asyncio.create_task(task.start())

        logger.info("Started periodic task")

        try:
            # Keep the main coroutine running
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Shutting down...")
        finally:
            r.close()
            logger.info("Redis connection closed")


async def shutdown(loop):
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s,%(msecs)03d %(name)-16s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    asyncio.run(main())
