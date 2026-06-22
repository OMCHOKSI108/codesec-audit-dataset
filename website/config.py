import os


class Config:
    SECRET_KEY = os.environ.get("SESSION_SECRET", os.urandom(32).hex())
    CODESEC_API_URL = os.environ.get("CODESEC_API_URL", "http://localhost:8000")
    PUBLIC_WEBSITE_URL = os.environ.get("PUBLIC_WEBSITE_URL", "http://localhost:5000")

    GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
    GITHUB_CALLBACK_URL = os.environ.get(
        "GITHUB_CALLBACK_URL", f"{PUBLIC_WEBSITE_URL}/auth/github/callback"
    )
    GITHUB_APP_SLUG = os.environ.get("GITHUB_APP_SLUG", "")

    MONGODB_URI = os.environ.get("MONGODB_URI", "")
    MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "codesec_audit")

    RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
    EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
    OWNER_CONTACT_EMAIL = os.environ.get("OWNER_CONTACT_EMAIL", "omchoksi108@gmail.com")

    FREE_PR_REVIEWS_PER_MONTH = int(os.environ.get("FREE_PR_REVIEWS_PER_MONTH", "30"))
