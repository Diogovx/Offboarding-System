from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = ""
    SECRET_KEY: str = ""
    ALGORITHM: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    INTOUCH_TOKEN: str = ""
    INTOUCH_URL: str = ""
    INTOUCH_API_KEY: str = "your_api_key_here"
    EMAIL_SENDER: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_RECEIVER: str = ""
    SMTP_SERVER: str = ""
    PORT: int = 587
    AD_USERNAME: str = "username_here"
    AD_PASSWORD: str = "password_here"
    AD_SERVER: str = ""
    AD_DOMAIN: str = ""
    AD_BASE_DN: str = ""
    DISABLED_OU: str = ""
    TURNSTILE_A_URL: str = ""
    TURNSTILE_A_SESSION: str = ""
    TURNSTILE_B_URL: str = ""
    TURNSTILE_B_SESSION: str = ""


@lru_cache
def get_settings():
    return Settings()

settings = get_settings()
