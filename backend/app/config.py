from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "verse-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str = "sqlite:///./verse.db"


settings = Settings()
