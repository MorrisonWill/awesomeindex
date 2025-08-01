from typing import Optional, List, Dict, Any
import httpx
import json
import re
import asyncio
import time
from datetime import datetime
from app.config import settings


class GitHubClient:
    """GitHub API client for fetching repository data"""

    def __init__(self):
        self.base_url = "https://api.github.com"
        self.token = settings.github_token
        self.client = httpx.AsyncClient(headers=self._get_headers(), timeout=30.0)
        self.rate_limit_remaining = None
        self.rate_limit_reset = None

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AwesomeIndex/1.0",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def _update_rate_limit(self, response: httpx.Response):
        """Update rate limit information from response headers"""
        headers = response.headers
        if "x-ratelimit-remaining" in headers:
            self.rate_limit_remaining = int(headers["x-ratelimit-remaining"])
        if "x-ratelimit-reset" in headers:
            self.rate_limit_reset = int(headers["x-ratelimit-reset"])

    async def _handle_rate_limit(self, response: httpx.Response):
        """Handle rate limit errors and wait if necessary"""
        if response.status_code == 403 and "x-ratelimit-remaining" in response.headers:
            if int(response.headers["x-ratelimit-remaining"]) == 0:
                reset_time = int(response.headers.get("x-ratelimit-reset", 0))
                if reset_time:
                    wait_time = reset_time - int(time.time()) + 1
                    if wait_time > 0:
                        reset_datetime = datetime.fromtimestamp(reset_time).strftime("%Y-%m-%d %H:%M:%S")
                        print(f"  ⏳ GitHub rate limit reached. Waiting {wait_time} seconds (until {reset_datetime})...")
                        await asyncio.sleep(wait_time)
                        print(f"  ✓ Rate limit reset. Continuing...")
                        return True
        return False

    async def check_rate_limit(self) -> Dict[str, Any]:
        """Check current rate limit status"""
        try:
            response = await self.client.get(f"{self.base_url}/rate_limit")
            response.raise_for_status()
            data = response.json()
            core_limits = data.get("rate", {})
            return {
                "limit": core_limits.get("limit", 0),
                "remaining": core_limits.get("remaining", 0),
                "reset": core_limits.get("reset", 0),
                "reset_datetime": datetime.fromtimestamp(core_limits.get("reset", 0)).isoformat()
            }
        except httpx.HTTPError:
            return {}

    async def get_repository(self, full_name: str) -> Optional[Dict[str, Any]]:
        """Get repository metadata from GitHub API"""
        for retry in range(3):
            try:
                response = await self.client.get(f"{self.base_url}/repos/{full_name}")
                self._update_rate_limit(response)
                
                if await self._handle_rate_limit(response):
                    continue
                    
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                if retry < 2:
                    await asyncio.sleep(1)
                    continue
                return None
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
        for retry in range(3):
            try:
                response = await self.client.get(
                    f"{self.base_url}/repos/{full_name}/readme"
                )
                self._update_rate_limit(response)
                
                if await self._handle_rate_limit(response):
                    continue
                    
                response.raise_for_status()
                readme_data = response.json()

                # Get raw content
                content_response = await self.client.get(readme_data["download_url"])
                content_response.raise_for_status()
                return content_response.text
            except httpx.HTTPError as e:
                if retry < 2:
                    await asyncio.sleep(1)
                    continue
                print(f"Error fetching README for {full_name}: {str(e)}")
                return None
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
