from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://bonusapp:bonusapp_secret@localhost:5432/bonusapp"
    secret_key: str = "change-me-in-production-min-32-chars!!"
    jwt_algorithm: str = "HS256"
    jwt_ttl_hours: int = 8
    hmac_secret: str = "change-hmac-secret-in-production"
    environment: str = "development"

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
