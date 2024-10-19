import signal

import redis
from config import config
from scheduler import PeriodicTask
from storage import Storage

from scraper import Scraper


async def main():
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(sig, loop)))

    print("Hello, World!")
    r = redis.from_url(config.redis.url, decode_responses=True)
    storage = Storage(r, config.redis.prefix)

    scraper = Scraper(config.scraper.url)

    task = PeriodicTask(
        scraper=scraper,
        storage=storage,
        interval=config.scraper.interval,
    )  # Run every 5 seconds
    asyncio.create_task(task.start())

    try:
        # Keep the main coroutine running
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("Cancelled!")
    finally:
        print("Bye!")


async def shutdown(sig, loop):
    print(f"Received signal {sig.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
