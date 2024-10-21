import hashlib
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag

if TYPE_CHECKING:
    from app.storage import Storage


class Record:
    area: str
    organization: str
    address: str
    dates: str

    hash: str

    def __init__(self, area: str, organization: str, address: str, dates: str):
        self.area = area
        self.organization = organization
        self.address = address
        self.dates = dates

        self.hash = (
            hashlib.md5((self.area + self.address + self.dates).encode()).digest().hex()
        )

    def __hash__(self) -> int:
        return hash(self.hash)

    def __repr__(self):
        return f"Record({self.area}, {self.organization}, {self.address}, {self.dates})"


@dataclass
class State:
    area: str | None
    today: bool


class Scraper:
    def __init__(self, url: str, storage: "Storage"):
        self.url = url
        self.storage = storage

    async def run(self) -> list[Record]:
        print("Running scraper...")

        if not await self.is_changed():
            print("ETag not changed, skipping scraping...")
            return []

        print("ETag changed, scraping...")
        response = httpx.get(self.url)
        response.encoding = "windows-1251"

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        table: Tag = soup.find("table")  # type: ignore
        state: State = State(area=None, today=True)

        # Print all rows with numbers
        records = []
        for row in table.find_all("tr"):
            text = row.text.strip()
            if not text:
                continue
            if "район" in text:
                state.area = self.collapse_whitespaces(text)
                state.today = True
                continue

            if state.area:
                records.append(self.process_area(state, row))

        records = list(filter(lambda x: x, records))

        return records

    async def is_changed(self) -> bool:
        response = httpx.head(self.url)
        response.raise_for_status()
        if "ETag" not in response.headers:
            return True

        return self.storage.is_etag_changed(response.headers["ETag"])

    def process_area(self, state: State, row: Tag) -> Record | None:
        text = row.text.strip()
        if "завтра" in text:
            state.today = False
            return None

        cells = row.find_all("td")
        if len(cells) != 3 or not cells[0].text.strip():
            return None

        organization = self.collapse_whitespaces(cells[0].text.strip())
        address = self.collapse_whitespaces(cells[1].text.strip())
        dates = self.collapse_whitespaces(cells[2].text.strip())

        return Record(state.area, organization, address, dates)

    def collapse_whitespaces(self, string):
        return re.sub(r"\s+", " ", string)
