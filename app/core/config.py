from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/currency_exchange"
    GROQ_API_KEY: str = ""
    APP_ENV: str = "development"
    APP_NAME: str = "Currency Exchange System"

    model_config = {"env_file": ".env"}


settings = Settings()
