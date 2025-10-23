from pydantic_settings import BaseSettings #tool for managing application configurations

class Settings(BaseSettings):
    APP_NAME: str  = "Natural Triade API"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./natural_triade.db"

    # Stripe Configuration
    STRIPE_SECRET_KEY: str = "sk_test_51..."  # Stripe test key
    STRIPE_PUBLISHABLE_KEY: str = "pk_test_51..."  # Para el frontend
    STRIPE_WEBHOOK_SECRET: str = "whsec_..."  # Webhook signing secret

    # Payment settings
    CURRENCY: str = "clp"  # Peso chileno

    class Config:
        env_file = ".env"

settings = Settings()

