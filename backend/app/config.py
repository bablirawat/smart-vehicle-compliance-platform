from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Vehicle Compliance & Journey Management Platform"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "super-secret-production-key-change-in-prod-123456789"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    DATABASE_URL: str = "sqlite:///./smart_vehicle.db"

    DEDUPLICATION_WINDOW_SECONDS: int = 60
    ANPR_CONFIDENCE_THRESHOLD: float = 0.85
    PERMIT_EXPIRING_SOON_DAYS: int = 30

    SIMULATOR_FAIL_PROBABILITY: float = 0.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
