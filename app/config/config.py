from dataclasses import dataclass
import os


@dataclass
class Redis:
    url: str


@dataclass
class Scraper:
    url: str
    interval: int


@dataclass
class Storage:
    ttl: int
    prefix: str


@dataclass
class Publisher:
    prefix: str


@dataclass
class Config:
    redis: Redis
    scraper: Scraper
    storage: Storage
    publisher: Publisher


config = Config(
    redis=Redis(
        url=os.environ.get("REDIS__URL", "redis://localhost:6379"),
    ),
    scraper=Scraper(
        url=os.environ.get("SCRAPER__URL", "http://93.92.65.26/aspx/Gorod.htm"),
        interval=int(os.environ.get("SCRAPER__INTERVAL", 5 * 60)),
    ),
    storage=Storage(
        ttl=int(os.environ.get("STORAGE__TTL_DAYS", 5)) * 24 * 60 * 60,
        prefix=os.environ.get(
            "STORAGE__PREFIX", os.environ.get("REDIS__PREFIX", "bot-005")
        ),
    ),
    publisher=Publisher(
        prefix=os.environ.get(
            "PUBLISHER__PREFIX", os.environ.get("REDIS__PREFIX", "bot-005")
        )
    ),
)
