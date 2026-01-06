from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Configuração para ler do .env se ele existir
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Definição das variáveis com Type Hints e valores padrão
    DATABASE_URL: str = ""
    SECRET_KEY: str = ""
    ALGORITHM: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 
    INTOUCH_TOKEN: str = ""
    INTOUCH_URL: str = ""
    INTOUCH_API_KEY: str = "your_api_key_here"
    EMAIL_SENDER: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_RECEIVER: str = ""
    SMTP_SERVER: str = ""
    PORT: int =