import hashlib
import logging
import random
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

OTP_LENGTH = 6
OTP_EXPIRE_MINUTES = 10
MAX_OTP_ATTEMPTS = 3
OTP_COOLDOWN_MINUTES = 10


class OTPError(Exception):
    pass


def generate_otp() -> str:
    return str(random.randint(10 ** (OTP_LENGTH - 1), 10**OTP_LENGTH - 1))


def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


def send_otp(user_id: str, email: str) -> str:
    from website.db import get_mongo
    from website.email_service import send_otp_email

    db, _ = get_mongo()

    now = datetime.now(timezone.utc)
    cooldown_start = now - timedelta(minutes=OTP_COOLDOWN_MINUTES)
    recent_count = db.email_otps_collection.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": cooldown_start},
    })
    if recent_count >= MAX_OTP_ATTEMPTS:
        raise OTPError("Too many OTP requests. Please try again later.")

    otp = generate_otp()
    otp_hash = hash_otp(otp)

    expires_at = now + timedelta(minutes=OTP_EXPIRE_MINUTES)
    db.email_otps_collection.insert_one({
        "user_id": user_id,
        "email": email,
        "otp_hash": otp_hash,
        "expires_at": expires_at,
        "attempts": 0,
        "created_at": now,
    })

    sent = send_otp_email(email, otp)
    if not sent:
        raise OTPError("Failed to send verification email. Please try again.")

    return otp


def verify_otp(user_id: str, otp: str) -> bool:
    from website.db import get_mongo

    db, _ = get_mongo()

    now = datetime.now(timezone.utc)
    otp_hash = hash_otp(otp)

    record = db.email_otps_collection.find_one({
        "user_id": user_id,
        "expires_at": {"$gte": now},
    })
    if not record:
        raise OTPError("No valid OTP found. Please request a new one.")

    if record.get("attempts", 0) >= MAX_OTP_ATTEMPTS:
        raise OTPError("Too many failed attempts. Please request a new OTP.")

    db.email_otps_collection.update_one(
        {"_id": record.get("_id", "")},
        {"$inc": {"attempts": 1}},
    )

    if record["otp_hash"] != otp_hash:
        raise OTPError("Invalid verification code.")

    db.users_collection.update_one(
        {"github_id": user_id},
        {"$set": {"email_verified": True}},
    )

    return True
