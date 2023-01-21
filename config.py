from pydantic import BaseSettings


class Settings(BaseSettings):
    API_VERSION: str
    API_TITLE: str
    BASE_URL: str

    REDIS_HOSTNAME: str
    REDIS_PORT: str
    REDIS_PASSWORD: str

    FIREBASE_SERVICE_ACCOUNT_CREDENTIALS_PATH: str

    class Config:
        env_file = ".env"


settings = Settings()
