from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Awesome Search"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./data/awesome_search.db"

    # MeiliSearch
    meilisearch_url: str = "http://localhost:7700"
    meilisearch_api_key: Optional[str] = None

    # GitHub API
    github_token: Optional[str] = None
    github_api_url: str = "https://api.github.com"

    # App settings
    items_per_page: int = 20
    max_search_results: int = 100

    class Config:
        env_file = ".env"


settings = Settings()
