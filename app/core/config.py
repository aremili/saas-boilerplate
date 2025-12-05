from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "SaaS Boilerplate"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False  # Controlled by env var, defaults to False for safety
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

