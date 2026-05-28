from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Calculus Visual Learning"
    secret_key: str = "change-me-in-production-use-env-var"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = "sqlite:///./calculus.db"
    cors_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"


settings = Settings()
