import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    APP_NAME = os.getenv("APP_NAME", "CodeSecAudit AI")
    APP_ENV = os.getenv("APP_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    PUBLIC_WEBSITE_URL = os.getenv("PUBLIC_WEBSITE_URL", "http://localhost:5000")
    CODESEC_API_URL = os.getenv("CODESEC_API_URL", "https://codesec-api.onrender.com")

    SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-secret-change-in-production")
    SESSION_TYPE = "filesystem"
    PERMANENT_SESSION_LIFETIME = 86400 * 7

    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID") or os.getenv("GITHUB_APP_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET") or os.getenv("GITHUB_APP_CLIENT_SECRET", "")
    GITHUB_CALLBACK_URL = os.getenv(
        "GITHUB_CALLBACK_URL",
        os.getenv("PUBLIC_WEBSITE_URL", "http://localhost:5000") + "/auth/github/callback",
    )
    GITHUB_APP_SLUG = os.getenv("GITHUB_APP_SLUG", "codesecaudit-ai")

    MONGODB_URI = os.getenv("MONGODB_URI", "")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "codereview")

    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
    EMAIL_FROM = os.getenv(
        "EMAIL_FROM",
        "CodeSecAudit AI <onboarding@resend.dev>",
    )
    OWNER_CONTACT_EMAIL = os.getenv("OWNER_CONTACT_EMAIL", "omchoksi108@gmail.com")

    FREE_PR_REVIEWS_PER_MONTH = int(os.getenv("FREE_PR_REVIEWS_PER_MONTH", "30"))
