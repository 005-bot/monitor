import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag

from app.parser import parse_dates

if TYPE_CHECKING:
    from app.storage import Storage

logger = logging.getLogger(__name__)


class Record:
    area: str
    organization: str
    address: str
    dates: list[datetime]

    def __init__(
        self, area: str, organization: str, address: str, dates: list[datetime]
    ):
        self.area = area
        self.organization = organization
        self.address = address
        self.dates = dates

    def __repr__(self):
        return f"Record({self.area}, {self.organization}, {self.address}, {self.dates})"


@dataclass
class State:
    area: str | None


class Scraper:
    def __init__(self, url: str, storage: "Storage"):
        self.url = url
        self.storage = storage

        self.session = httpx.AsyncClient()

    async def run(self) -> list[Record]:
        logger.info("Running scraper...")

        if not await self.is_changed():
            logger.info("ETag not changed, skipping scraping...")
            return []

        logger.info("ETag changed, scraping...")
        response = await self.session.get(self.url)  # httpx.get(self.url)
        response.encoding = "windows-1251"

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        table: Tag = soup.find("table")  # type: ignore
        state: State = State(area=None)

        # Print all rows with numbers
        records = []
        for row in table.find_all("tr"):
            text = row.text.strip()
            if not text:
                continue

            cells = row.find_all("td")
            if len(cells) != 3:
                logger.debug("Skipping row: %s", text)
                continue

            if (
                not cells[0].text.strip()
                and "район" in cells[1].text
                and not cells[2].text.strip()
            ):
                state.area = self.collapse_whitespaces(cells[1].text)
                continue

            if state.area:
                records.append(self.process_area(state.area, cells))

        records = list(filter(lambda x: x, records))

        return records

    async def is_changed(self) -> bool:
        response = httpx.head(self.url)
        response.raise_for_status()
        if "ETag" not in response.headers:
            logger.warning("ETag not found, scraping anyway.")
            return True

        return await self.storage.is_etag_changed(response.headers["ETag"])

    def process_area(self, area: str, cells: tuple[Tag, Tag, Tag]) -> Record | None:
        if not all(cell.text.strip() for cell in cells):
            logger.debug(
                "Skipping row: %s", "|".join(cell.text.strip() for cell in cells)
            )
            return None

        organization = self.collapse_whitespaces(cells[0].text.strip())
        address = self.collapse_whitespaces(cells[1].text.strip())
        dates = self.collapse_whitespaces(cells[2].text.strip())

        parsed_dates = parse_dates(dates)

        return Record(area, organization, address, parsed_dates)

    def collapse_whitespaces(self, string):
        return re.sub(r"\s+", " ", string)
