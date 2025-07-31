from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Awesome Search"
    debug: bool = False
    database_url: str = "sqlite:///./awesomesearch.db"
    meilisearch_url: str = "http://localhost:7700"
    meilisearch_api_key: Optional[str] = None
    github_token: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
