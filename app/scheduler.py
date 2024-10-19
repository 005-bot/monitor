import asyncio

from storage import Storage
from scraper import Scraper


class PeriodicTask:
    def __init__(self, scraper: Scraper, storage: Storage, interval: int):
        self.scraper = scraper
        self.interval = interval
        self.is_running = False

        self.storage = storage

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
        records = await self.scraper.run()

        print(self.storage.diff(records))
