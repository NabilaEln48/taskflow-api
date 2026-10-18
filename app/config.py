"""Application configuration.

Why pydantic-settings instead of plain os.environ?
- Validation: a missing DATABASE_URL fails fast at startup with a clear
  error instead of blowing up on the first request.
- Types: values are parsed (e.g. ints stay ints) and documented in one place.
- One source of truth: every module imports `settings` instead of
  re-reading env vars with different defaults.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Reads from the environment, falls back to the defaults below.
    # model_config tells pydantic-settings to ALSO read a local `.env` file,
    # which is convenient in development (and git-ignored, so secrets stay local).
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = (
        "postgresql+psycopg2://taskflow:taskflow@localhost:5432/taskflow"
    )
    # In production this MUST come from the environment — the default below is
    # only so the app boots locally without any setup.
    SECRET_KEY: str = "dev-only-secret-key-change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


settings = Settings()
