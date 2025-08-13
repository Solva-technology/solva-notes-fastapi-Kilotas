from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Note App"
    APP_VERSION: str = "0.1.0"
    APP_DEBUG: bool = True

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,   # ключи окружения читаются без учёта регистра
        extra="ignore"          # лишние переменные не валят приложение
    )

settings = Settings()
