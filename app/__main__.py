import asyncio
import signal

import redis

from app.config import config
from app.publisher import Publisher
from app.scheduler import PeriodicTask
from app.scraper import Scraper
from app.storage import Storage


async def main():
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(sig, loop)))

    r = redis.from_url(config.redis.url, decode_responses=True)
    storage = Storage(r, config.redis.prefix)
    publisher = Publisher(r, config.redis.prefix)

    scraper = Scraper(config.scraper.url, storage=storage)

    task = PeriodicTask(
        scraper=scraper,
        storage=storage,
        publisher=publisher,
        interval=config.scraper.interval,
    )
    asyncio.create_task(task.start())

    try:
        # Keep the main coroutine running
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("Cancelled!")
    finally:
        r.close()
        print("Bye!")


async def shutdown(sig, loop):
    print(f"Received signal {sig.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


if __name__ == "__main__":
    asyncio.run(main())
