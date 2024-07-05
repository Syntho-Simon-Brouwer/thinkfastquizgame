from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    JWT_SECRET: str = "please_please_update_me_please"
    JWT_ALGORITHM: str = "HS256"

    DATABASE_URI: str = "postgresql+asyncpg://postgres:password@0.0.0.0:5432/appdev"


settings = Settings()
