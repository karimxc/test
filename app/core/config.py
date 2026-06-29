from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    GROQ_API_KEY: str = ""
    APP_ENV: str = "development"
    APP_NAME: str = "Currency Exchange System"

    model_config = {"env_file": ".env"}

    @property
    def db_url(self) -> str:
        url = self.DATABASE_URL
        if not url:
            raise RuntimeError(
                "DATABASE_URL is not set. "
                "Add it to your .env file (local) or Railway Variables (production)."
            )
        # Railway sometimes provides postgres:// — SQLAlchemy requires postgresql://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url


settings = Settings()
