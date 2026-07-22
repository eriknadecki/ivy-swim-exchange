from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://ivyswim:ivyswim@localhost:5432/ivyswim"
    jwt_secret: str = "change-me-in-production-to-a-random-32-byte-value"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    starting_balance_cents: int = 1_000_000
    cors_allow_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


settings = Settings()
