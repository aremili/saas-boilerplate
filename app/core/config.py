from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "SaaS Boilerplate"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False  # Controlled by env var, defaults to False for safety
    DATABASE_URL: str = "postgresql+asyncpg://saas:saas_password@localhost:5432/saas_db"

    # PostgreSQL connection pool settings
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # PostgreSQL Credentials (for testing and manual construction)
    POSTGRES_USER: str = "saas"
    POSTGRES_PASSWORD: str = "saas_password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "saas_db"

    # Authentication
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Logging configuration
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "console"  # "json" for production, "console" for development

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
