import os
from datetime import datetime, timezone
from website.config import Config

_users: dict[str, dict] = {}
_mongo = None
_mongo_db = None


def _get_mongo():
    global _mongo, _mongo_db
    if _mongo is None and Config.MONGODB_URI:
        try:
            from pymongo import MongoClient
            _mongo = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=3000)
            _mongo.admin.command("ping")
            _mongo_db = _mongo[Config.MONGODB_DB_NAME]
        except Exception:
            _mongo = False
    return _mongo_db if _mongo and _mongo is not False else None


def is_mongo_connected() -> bool:
    return _get_mongo() is not None


def upsert_user(github_id: str, data: dict) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    data["github_id"] = github_id
    data["last_login_at"] = now

    db = _get_mongo()
    if db:
        existing = db.users.find_one({"github_id": github_id})
        if existing:
            db.users.update_one({"github_id": github_id}, {"$set": data, "$setOnInsert": {"created_at": now}})
            merged = {**existing, **data}
        else:
            data["created_at"] = now
            db.users.insert_one(data)
            merged = data
        return merged

    existing = _users.get(github_id)
    if existing:
        existing.update(data)
        return existing
    data["created_at"] = now
    _users[github_id] = data
    return data


def get_user(github_id: str) -> dict | None:
    db = _get_mongo()
    if db:
        return db.users.find_one({"github_id": github_id}, {"_id": 0})
    return _users.get(github_id)


def update_usage(github_id: str, reviews_used: int) -> None:
    db = _get_mongo()
    if db:
        db.users.update_one(
            {"github_id": github_id},
            {"$set": {"reviews_used": reviews_used}}
        )
        return
    user = _users.get(github_id)
    if user:
        user["reviews_used"] = reviews_used
