from pydantic import BaseSettings


class Settings(BaseSettings):
    API_VERSION: str
    API_TITLE: str
    BASE_URL: str

    class Config:
        env_file = ".env"


settings = Settings()
