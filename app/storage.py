import asyncio
import hashlib
import logging
import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Awaitable, Literal, TypeVar

from redis import Redis

from app.parser import format_dates
from app.publisher import ParsedRecord
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
        self.key_records = f"{prefix}:records"

        self.re_non_word = re.compile(r"\W")

    async def migrate(self):
        pass

    async def is_etag_changed(self, etag: str | None) -> bool:
        if etag is None:
            return True

        return (await result(self.r.set(self.key_etag, etag, get=True))) != etag

    async def diff(self, records: list[ParsedRecord]) -> list[ParsedRecord]:
        """
        Compares a list of new records with stored records and returns a list of records
        that are considered new or changed.

        This method checks if the given records are already present in the storage by
        comparing their hashes. If a record is not present, it is considered changed.
        Additionally, it filters out records that have addresses similar to any stored
        records using a similarity threshold, identifying them as not new.

        Args:
            records (list[Record]): A list of records to be compared with stored records.

        Returns:
            list[Record]: A list of records that are new or changed compared to stored records.
        """
        if not records:
            return []

        logger.info("Before diff %d records", len(records))
        hashes = [self.hash(record) for record in records]
        members: list[Literal[0, 1]] = await result(
            self.r.smismember(self.key_hashes, hashes)
        )

        changed = [
            record for record, is_member in zip(records, members) if not is_member
        ]

        logger.info("After hash filter %d records", len(changed))

        if len(changed) == 0:
            return changed

        stored: dict[str, Record] = {
            k: Record.model_validate_json(v)
            for k, v in (await result(self.r.hgetall(self.key_records))).items()
        }

        logger.info(
            "Diffing %d records with %d stored records", len(changed), len(stored)
        )

        def is_new(stored: list[ParsedRecord]):
            """
            Return a function that checks if a record is new or not.

            The function takes a `Record` as argument and checks if its address is
            similar to any of the addresses in the `stored` list. If the similarity
            ratio is greater than 0.8, it returns `False`. Otherwise, it returns
            `True`.
            """

            s = SequenceMatcher()

            def f(record: ParsedRecord):
                """
                Return True if record.address is not similar to any of the addresses in the stored list.
                Otherwise, return False.

                Similarity is checked using SequenceMatcher.ratio() with a threshold of 0.8.
                """
                s.set_seq2(record.address)
                for stored_record in stored:
                    s.set_seq1(stored_record.address)
                    ratio = s.ratio()
                    if ratio > 0.8 and stored_record.dates[-1] == record.dates[-1]:
                        logger.info(
                            "Skipping record %s as similar to %s with ratio %.2f",
                            record,
                            stored_record,
                            ratio,
                        )
                        return False
                return True

            return f

        changed = list(filter(is_new(stored.values()), changed))  # type: ignore

        logger.info("After diff filter %d records", len(changed))

        return changed

    async def commit(self, records: list[ParsedRecord]):
        """
        Commits a list of records to the storage.

        The method stores the hashes of the records in the `hashes` set,
        their timestamps in the `ttls` sorted set and the records themselves
        in the `records` hash map.

        After that, it removes outdated records from the storage by
        looking for records that have a timestamp older than the given TTL
        in the `ttls` sorted set. If such records are found, they are removed
        from the `hashes` set, the `ttls` sorted set and the `records` hash map.

        Args:
            records (list[Record]): A list of records to be stored in the storage.
        """
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
        await result(
            pipe.hmset(
                self.key_records,
                dict(zip(hashes, [record.model_dump_json() for record in records])),
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
        await result(pipe.hdel(self.key_records, *to_remove))
        pipe.execute()

    def hash(self, record: ParsedRecord) -> str:
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
