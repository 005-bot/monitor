from dataclasses import dataclass
import os


@dataclass
class Redis:
    url: str
    prefix: str


@dataclass
class Scraper:
    url: str
    interval: int


@dataclass
class Config:
    redis: Redis
    scraper: Scraper


config = Config(
    redis=Redis(
        url=os.environ.get("REDIS__URL", "redis://localhost:6379"),
        prefix=os.environ.get("REDIS__PREFIX", "bot-005"),
    ),
    scraper=Scraper(
        url=os.environ.get("SCRAPER__URL", "http://93.92.65.26/aspx/Gorod.htm"),
        interval=int(os.environ.get("SCRAPER__INTERVAL", 5 * 60)),
    ),
)
