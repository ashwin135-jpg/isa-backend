from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "ISA Backend"
    API_V1_PREFIX: str = "/api"

    class Config:
        env_file = ".env"


settings = Settings()
