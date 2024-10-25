import asyncio
import hashlib
import logging
import re
from datetime import datetime
from typing import Awaitable, Literal, TypeVar

from redis import Redis

from app.parser import format_dates
from app.scraper import Record

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def result(value: T | Awaitable[T]) -> T:
    if asyncio.iscoroutine(value):
        return await value
    return value  # type: ignore


class Storage:
    def __init__(self, r: Redis, prefix: str, ttl: int):
        self.r = r
        self.prefix = prefix
        self.ttl = ttl

        self.key_etag = f"{prefix}:etag"
        self.key_hashes = f"{prefix}:items"
        self.key_ttls = f"{prefix}:ttls"

        self.re_non_word = re.compile(r"\W")

    async def migrate(self):
        pass

    async def is_etag_changed(self, etag: str | None) -> bool:
        if etag is None:
            return True

        return (await result(self.r.set(self.key_etag, etag, get=True))) != etag

    async def diff(self, records: list[Record]) -> list[Record]:
        if not records:
            return []

        hashes = [self.hash(record) for record in records]
        members: list[Literal[0, 1]] = await result(
            self.r.smismember(self.key_hashes, hashes)
        )

        return [record for record, is_member in zip(records, members) if not is_member]

    async def commit(self, records: list[Record]):
        if not records:
            return

        hashes = [self.hash(record) for record in records]

        pipe = self.r.pipeline()

        await result(pipe.sadd(self.key_hashes, *hashes))
        await result(
            pipe.zadd(
                self.key_ttls,
                {self.hash(record): datetime.now().timestamp() for record in records},
            )
        )
        pipe.execute()

        to_remove = await result(
            self.r.zrangebyscore(
                self.key_ttls, 0, datetime.now().timestamp() - self.ttl
            )
        )
        if not to_remove:
            return

        logger.info("Removing %d outdated records", len(to_remove))

        pipe = self.r.pipeline()
        await result(pipe.zrem(self.key_ttls, *to_remove))
        await result(pipe.srem(self.key_hashes, *to_remove))
        pipe.execute()

    def hash(self, record: Record) -> str:
        return (
            hashlib.md5(
                (
                    record.area
                    + self.re_non_word.sub("", record.address)
                    + format_dates(record.dates)
                ).encode()
            )
            .digest()
            .hex()
        )
