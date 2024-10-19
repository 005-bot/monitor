from dataclasses import dataclass
import hashlib
import re
import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag


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
            hashlib.md5(
                (self.area + self.organization + self.address + self.dates).encode()
            )
            .digest()
            .hex()
        )

    def __repr__(self):
        return f"Record({self.area}, {self.organization}, {self.address}, {self.dates})"


@dataclass
class State:
    area: str | None
    today: bool


class Scraper:
    def __init__(self, url):
        self.url = url

    async def run(self) -> list[Record]:
        print("Running scraper...")
        response = httpx.get(self.url)
        response.encoding = "windows-1251"

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
        for record in records:
            print(record)
        print(len(records))

        return records

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
