import os

SECRET_KEY = os.getenv("SECRET_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")

# Deepseek (OpenAI-compatible) configuration for the automatic pass review.
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# CORS: comma separated list of origins, defaults to any origin.
CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
    if origin.strip()
]

# Simple in-memory rate limiting for the authentication endpoints.
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() not in {
    "0",
    "false",
    "no",
}
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))


def validate_settings() -> None:
    """Fail fast when required settings are missing."""
    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY environment variable is required to sign authentication tokens"
        )
