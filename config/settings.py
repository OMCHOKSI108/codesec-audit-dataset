import os
from functools import lru_cache

from pydantic import BaseModel, Field


class _Settings(BaseModel):
    app_env: str = Field(
        default_factory=lambda: os.getenv("APP_ENV", "development"),
        description="Application environment (development, staging, production)",
    )
    public_website_url: str = Field(
        default_factory=lambda: os.getenv("PUBLIC_WEBSITE_URL", "http://localhost:8003"),
    )
    api_base_url: str = Field(
        default_factory=lambda: os.getenv("API_BASE_URL", "http://localhost:8003"),
    )
    dashboard_url: str = Field(
        default_factory=lambda: os.getenv("DASHBOARD_URL", "http://localhost:8502"),
    )
    cors_origins: str = Field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:8501,http://localhost:8502"),
    )

    mongodb_uri: str = Field(
        default_factory=lambda: os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
    )
    mongodb_db_name: str = Field(
        default_factory=lambda: os.getenv("MONGODB_DB_NAME", "codesecaudit"),
    )

    github_app_id: str = Field(
        default_factory=lambda: os.getenv("GITHUB_APP_ID", ""),
    )
    github_client_id: str = Field(
        default_factory=lambda: os.getenv("GITHUB_CLIENT_ID", ""),
    )
    github_client_secret: str = Field(
        default_factory=lambda: os.getenv("GITHUB_CLIENT_SECRET", ""),
    )
    github_webhook_secret: str = Field(
        default_factory=lambda: os.getenv("GITHUB_WEBHOOK_SECRET", ""),
    )
    github_private_key_base64: str = Field(
        default_factory=lambda: os.getenv("GITHUB_PRIVATE_KEY_BASE64", ""),
    )

    jwt_secret: str = Field(
        default_factory=lambda: os.getenv("JWT_SECRET", "change-me"),
    )
    session_secret: str = Field(
        default_factory=lambda: os.getenv("SESSION_SECRET", "change-me"),
    )
    encryption_key: str = Field(
        default_factory=lambda: os.getenv("ENCRYPTION_KEY", ""),
    )
    access_token_expire_minutes: int = Field(
        default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")),
    )

    free_pr_reviews_per_month: int = Field(
        default_factory=lambda: int(os.getenv("FREE_PR_REVIEWS_PER_MONTH", "30")),
    )
    default_plan: str = Field(
        default_factory=lambda: os.getenv("DEFAULT_PLAN", "free"),
    )
    usage_window_days: int = Field(
        default_factory=lambda: int(os.getenv("USAGE_WINDOW_DAYS", "30")),
    )
    limit_action: str = Field(
        default_factory=lambda: os.getenv("LIMIT_ACTION", "block"),
    )

    resend_api_key: str = Field(
        default_factory=lambda: os.getenv("RESEND_API_KEY", ""),
    )
    email_from: str = Field(
        default_factory=lambda: os.getenv("EMAIL_FROM", "CodeSecAudit <noreply@codesecaudit.ai>"),
    )
    owner_contact_email: str = Field(
        default_factory=lambda: os.getenv("OWNER_CONTACT_EMAIL", "omchoksi108@gmail.com"),
    )

    codesec_enable_rag: bool = Field(
        default_factory=lambda: os.getenv("CODESEC_ENABLE_RAG", "false").lower() in ("1", "true", "yes"),
    )
    codesec_rag_mode: str = Field(
        default_factory=lambda: os.getenv("CODESEC_RAG_MODE", "local"),
        description="RAG mode: local (ChromaDB) or remote (HF Space)",
    )
    codesec_rag_service_url: str = Field(
        default_factory=lambda: os.getenv("CODESEC_RAG_SERVICE_URL", ""),
        description="Remote RAG service URL (used when CODESEC_RAG_MODE=remote)",
    )
    codesec_rag_api_key: str = Field(
        default_factory=lambda: os.getenv("CODESEC_RAG_API_KEY", ""),
    )
    codesec_rag_timeout: int = Field(
        default_factory=lambda: int(os.getenv("CODESEC_RAG_TIMEOUT", "15")),
    )
    codesec_max_files_per_pr: int = Field(
        default_factory=lambda: int(os.getenv("CODESEC_MAX_FILES_PER_PR", "30")),
    )
    codesec_max_file_size_kb: int = Field(
        default_factory=lambda: int(os.getenv("CODESEC_MAX_FILE_SIZE_KB", "200")),
    )
    codesec_max_inline_comments: int = Field(
        default_factory=lambda: int(os.getenv("CODESEC_MAX_INLINE_COMMENTS", "10")),
    )
    codesec_default_top_k: int = Field(
        default_factory=lambda: int(os.getenv("CODESEC_DEFAULT_TOP_K", "3")),
    )
    codesec_block_on_request_changes: bool = Field(
        default_factory=lambda: os.getenv("CODESEC_BLOCK_ON_REQUEST_CHANGES", "false").lower() in ("1", "true", "yes"),
    )

    admin_emails: str = Field(
        default_factory=lambda: os.getenv("ADMIN_EMAILS", "omchoksi108@gmail.com"),
    )
    allow_manual_limit_increase: bool = Field(
        default_factory=lambda: os.getenv("ALLOW_MANUAL_LIMIT_INCREASE", "true").lower() in ("1", "true", "yes"),
    )
    default_extra_pr_limit: int = Field(
        default_factory=lambda: int(os.getenv("DEFAULT_EXTRA_PR_LIMIT", "20")),
    )

    class Config:
        frozen = True


@lru_cache
def get_settings() -> _Settings:
    return _Settings()
