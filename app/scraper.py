import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString
from pydantic import BaseModel

from app.parser import parse_dates

if TYPE_CHECKING:
    from app.storage import Storage

logger = logging.getLogger(__name__)

_WS_RE = re.compile(r"\s+")


class Record(BaseModel):
    area: str
    organization: str
    address: str
    dates: list[datetime]

    def __repr__(self):
        return f"Record({self.area}, {self.organization}, {self.address}, {self.dates})"


@dataclass
class State:
    area: str | None


class Scraper:
    def __init__(self, url: str, storage: "Storage"):
        self.url = url
        self.storage = storage

        self._session: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._session = await httpx.AsyncClient().__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._session:
            await self._session.__aexit__(exc_type, exc_value, traceback)

    async def run(self) -> list[Record]:
        if not self._session:
            raise RuntimeError("HTTP client is not initialized")

        logger.info("Running scraper...")

        if not await self.is_changed():
            logger.info("ETag not changed, skipping scraping...")
            return []

        logger.info("ETag changed, scraping...")
        response = await self._session.get(self.url)  # httpx.get(self.url)
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
        if not self._session:
            raise RuntimeError("HTTP client is not initialized")

        response = await self._session.head(self.url)
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
        address = self.get_text(cells[1])
        dates = self.collapse_whitespaces(cells[2].text.strip())

        parsed_dates = parse_dates(dates)

        return Record(
            area=area,
            organization=organization,
            address="\n".join([s.strip() for s in address.splitlines()]),
            dates=parsed_dates,
        )

    @classmethod
    def collapse_whitespaces(cls, string):
        return _WS_RE.sub(" ", string)

    @classmethod
    def get_text(cls, tag: Tag) -> str:
        def _get_text(tag: Tag):
            for child in tag.children:
                # print(child)
                if isinstance(child, NavigableString):
                    yield cls.collapse_whitespaces(child.get_text())
                elif isinstance(child, Tag):
                    yield from ["\n"] if child.name == "br" else _get_text(child)

        return "".join(_get_text(tag))
