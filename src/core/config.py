from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    POSTGRES_HOST: str
    DB_PORT: int = 5432
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    TRAVELPAYOUTS_TOKEN: str
    DOCS_USERNAME: str
    DOCS_PASSWORD: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
