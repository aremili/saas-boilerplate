from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "SaaS Boilerplate"
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    ENVIRONMENT: str = "development"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
