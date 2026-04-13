from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://bonusapp:bonusapp_secret@localhost:5432/bonusapp"
    secret_key: str = "change-me-in-production-min-32-chars!!"
    jwt_algorithm: str = "HS256"
    jwt_ttl_hours: int = 8
    hmac_secret: str = "change-hmac-secret-in-production"
    environment: str = "development"
    # Przecinkowa lista kluczy POS — np. "key1,key2,key3"
    pos_api_keys: str = "pos-key-terminal-001,pos-key-terminal-002,pos-key-terminal-dev"

    @property
    def pos_api_keys_set(self) -> set[str]:
        return {k.strip() for k in self.pos_api_keys.split(",") if k.strip()}

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
