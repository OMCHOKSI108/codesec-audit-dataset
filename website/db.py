import hashlib
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class MemDB:
    def __init__(self):
        self.users: dict[str, dict] = {}
        self.email_otps: dict[str, dict] = {}
        self.email_events: list[dict] = []

    @property
    def users_collection(self):
        return _MemCollection(self.users)

    @property
    def email_otps_collection(self):
        return _MemCollection(self.email_otps)

    @property
    def email_events_collection(self):
        return _MemCollectionList(self.email_events)


class _MemCollection:
    def __init__(self, store: dict):
        self._store = store

    def find_one(self, filter_dict: dict) -> dict | None:
        for item in self._store.values():
            if all(item.get(k) == v for k, v in filter_dict.items()):
                return item
        return None

    def update_one(self, filter_dict: dict, update_dict: dict, upsert: bool = False):
        existing = self.find_one(filter_dict)
        if existing:
            if "$set" in update_dict:
                existing.update(update_dict["$set"])
            if "$inc" in update_dict:
                for k, v in update_dict["$inc"].items():
                    existing[k] = existing.get(k, 0) + v
            return type("Obj", (), {"matched_count": 1, "modified_count": 1})()
        if upsert:
            new_doc = {**filter_dict}
            if "$set" in update_dict:
                new_doc.update(update_dict["$set"])
            key = str(hash(frozenset(filter_dict.items())))
            self._store[key] = new_doc
            return type("Obj", (), {"matched_count": 0, "modified_count": 1, "upserted_id": key})()
        return type("Obj", (), {"matched_count": 0, "modified_count": 0})()

    def insert_one(self, doc: dict):
        key = str(id(doc))
        self._store[key] = doc
        return type("Obj", (), {"inserted_id": key})()

    def count_documents(self, filter_dict: dict | None = None) -> int:
        if filter_dict is None:
            return len(self._store)
        return sum(1 for v in self._store.values() if all(v.get(k) == val for k, val in filter_dict.items()))

    def find(self, filter_dict: dict | None = None, sort: list | None = None, limit: int = 0):
        items = list(self._store.values())
        if filter_dict:
            items = [v for v in items if all(v.get(k) == val for k, val in filter_dict.items())]
        return _MemCursor(items, sort, limit)


class _MemCollectionList:
    def __init__(self, store: list):
        self._store = store

    def insert_one(self, doc: dict):
        self._store.append(doc)
        return type("Obj", (), {"inserted_id": str(id(doc))})()

    def count_documents(self, filter_dict: dict | None = None) -> int:
        if filter_dict is None:
            return len(self._store)
        return sum(1 for v in self._store if all(v.get(k) == val for k, val in filter_dict.items()))

    def find(self, filter_dict: dict | None = None, sort: list | None = None, limit: int = 0):
        items = list(self._store)
        if filter_dict:
            items = [v for v in items if all(v.get(k) == val for k, val in filter_dict.items())]
        return _MemCursor(items, sort, limit)


class _MemCursor:
    def __init__(self, items: list, sort: list | None = None, limit: int = 0):
        self._items = items
        if sort:
            for key, direction in sort:
                self._items.sort(key=lambda x, k=key: x.get(k, ""), reverse=(direction == -1))
        if limit:
            self._items = self._items[:limit]

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)


_mem_db = MemDB()


def get_mongo() -> tuple:
    try:
        from pymongo import MongoClient
        from website.config import Config

        uri = Config.MONGODB_URI
        if not uri:
            logger.warning("MONGODB_URI not set, using in-memory fallback")
            return _mem_db, "mem"
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        db = client[Config.MONGODB_DB_NAME]
        logger.info("Connected to MongoDB Atlas")
        return db, "mongo"
    except Exception as e:
        logger.warning(f"MongoDB unavailable, using in-memory fallback: {e}")
        return _mem_db, "mem"


def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


def utcnow():
    return datetime.now(timezone.utc)
