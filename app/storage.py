from datetime import datetime
import logging
from redis import Redis

from app.scraper import Record

logger = logging.getLogger(__name__)


class Storage:
    def __init__(self, r: Redis, prefix: str, ttl: int):
        self.r = r
        self.prefix = prefix
        self.ttl = ttl

        self.key_etag = f"{prefix}:etag"
        self.key_hashes = f"{prefix}:items"
        self.key_ttls = f"{prefix}:ttls"

    def is_etag_changed(self, etag: str | None) -> bool:
        if etag is None:
            return True

        return self.r.set(self.key_etag, etag, get=True) != etag

    def diff(self, records: list[Record]) -> list[Record]:
        if not records:
            return []

        hashes = [record.hash for record in records]
        members = self.r.smismember(self.key_hashes, hashes)

        return [record for record, is_member in zip(records, members) if not is_member]

    def commit(self, records: list[Record]):
        if not records:
            return

        hashes = [record.hash for record in records]

        pipe = self.r.pipeline()

        # self.r.delete(self.key_hashes)
        pipe.sadd(self.key_hashes, *hashes)
        pipe.zadd(
            self.key_ttls,
            {record.hash: datetime.now().timestamp() for record in records},
        )
        pipe.execute()

        to_remove = self.r.zrangebyscore(
            self.key_ttls, 0, datetime.now().timestamp() - self.ttl
        )
        if not to_remove:
            return

        logger.info(f"Removing %d outdated records", len(to_remove))

        pipe = self.r.pipeline()
        pipe.zrem(self.key_ttls, *to_remove)
        pipe.srem(self.key_hashes, *to_remove)
        pipe.execute()
