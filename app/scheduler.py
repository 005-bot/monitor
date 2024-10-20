import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.storage import Storage
    from app.scraper import Scraper
    from app.publisher import Publisher


class PeriodicTask:
    def __init__(
        self,
        scraper: "Scraper",
        storage: "Storage",
        publisher: "Publisher",
        interval: int,
    ):
        self.scraper = scraper
        self.storage = storage
        self.publisher = publisher

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
        # Your periodic task logic goes here
        print("Running periodic task...")

        try:
            records = await self.scraper.run()
            changes = self.storage.diff(records)
            if not changes:
                return

            print("Changes:")
            for record in changes:
                print(record)

            for record in changes:
                try:
                    await self.publisher.publish(record)
                except Exception as e:
                    print(f"Failed to publish outage: {e}")
                    records.remove(record)

            self.storage.commit(records)
        except Exception as e:
            print(f"Failed to commit records: {e}")
