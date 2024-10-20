from redis import Redis

from app.scraper import Record


class Storage:
    def __init__(self, r: Redis, prefix: str):
        self.r = r
        self.prefix = prefix

        self.key_etag = f"{prefix}:etag"
        self.key_hashes = f"{prefix}:items"

    def is_etag_changed(self, etag: str | None) -> bool:
        print(f"ETag: {etag}")
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

        self.r.delete(self.key_hashes)
        self.r.sadd(self.key_hashes, *hashes)
