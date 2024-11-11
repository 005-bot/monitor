from contextlib import contextmanager
from datetime import datetime
import locale
import re

LOCALE_RUSSIAN = "ru_RU.UTF-8"
DATE_PATTERN = r"(\d{1,2})\s+(\w+)\s+(\d{2})[-:](\d{2})"


@contextmanager
def setlocale(name):
    saved = locale.setlocale(locale.LC_ALL)
    try:
        yield locale.setlocale(locale.LC_ALL, name)
    finally:
        locale.setlocale(locale.LC_ALL, saved)


def parse_dates(dates: str) -> list[datetime]:
    current_year = datetime.now().year
    found = re.findall(DATE_PATTERN, dates)

    with setlocale(LOCALE_RUSSIAN):
        return [
            datetime.strptime(
                f"{day} {month} {current_year} {hour.replace('24', '23')}:{minutes if hour != '24' else '59'}",
                "%d %B %Y %H:%M",
            )
            for day, month, hour, minutes in found
        ]


def format_dates(dates: list[datetime]) -> str:
    with setlocale(LOCALE_RUSSIAN):
        return " ".join([date.strftime("%d %B %H-%M").lower() for date in dates])
