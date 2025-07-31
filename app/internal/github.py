from typing import Optional, List, Dict, Any
import httpx
import json
import re
from app.config import settings


class GitHubClient:
    """GitHub API client for fetching repository data"""

    def __init__(self):
        self.base_url = "https://api.github.com"
        self.token = settings.github_token
        self.client = httpx.AsyncClient(headers=self._get_headers(), timeout=30.0)

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AwesomeIndex/1.0",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    async def get_repository(self, full_name: str) -> Optional[Dict[str, Any]]:
        """Get repository metadata from GitHub API"""
        try:
            response = await self.client.get(f"{self.base_url}/repos/{full_name}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return None

    async def search_awesome_repositories(
        self, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search for repositories with 'awesome' in the name"""
        try:
            params = {
                "q": "awesome in:name",
                "sort": "stars",
                "order": "desc",
                "per_page": min(limit, 100),
            }
            response = await self.client.get(
                f"{self.base_url}/search/repositories", params=params
            )
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])
        except httpx.HTTPError:
            return []

    async def get_readme_content(self, full_name: str) -> Optional[str]:
        """Get README content from repository"""
        try:
            response = await self.client.get(
                f"{self.base_url}/repos/{full_name}/readme"
            )
            response.raise_for_status()
            readme_data = response.json()

            # Get raw content
            content_response = await self.client.get(readme_data["download_url"])
            content_response.raise_for_status()
            return content_response.text
        except httpx.HTTPError:
            print(f"Error fetching README for {full_name}: {response.text}")
            return None

    async def get_repository_metadata(self, full_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive repository metadata including stars, language, topics"""
        repo_data = await self.get_repository(full_name)
        if not repo_data:
            return None

        return {
            "stars": repo_data.get("stargazers_count", 0),
            "language": repo_data.get("language"),
            "topics": repo_data.get("topics", []),
            "updated_at": repo_data.get("updated_at"),
        }


    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global client instance
github_client = GitHubClient()
