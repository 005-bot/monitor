from redis import Redis

from scraper import Record


class Storage:
    def __init__(self, r: Redis, key: str):
        self.r = r
        self.key = key

    def diff(self, records: list[Record]) -> list[Record]:
        hashes = [record.hash for record in records]
        members = self.r.smismember(self.key, hashes)
        self.r.sadd(self.key, *hashes)

        print(members)

        return [record for record, is_member in zip(records, members) if not is_member]
