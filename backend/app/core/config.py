from pydantic_settings import BaseSettings #tool for managing application configurations

class Settings(BaseSettings):
    APP_NAME: str  = "Natural Triade API"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./natural_triade.db"

    class Config:
        env_file = ".env"

settings = Settings()

