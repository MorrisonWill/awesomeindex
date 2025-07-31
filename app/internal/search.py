from typing import List, Dict, Any, Optional
from meilisearch_python_sdk import AsyncClient
from app.config import settings


class SearchService:
    """MeiliSearch integration service"""

    def __init__(self):
        self.url = settings.meilisearch_url
        self.api_key = settings.meilisearch_api_key
        self.index_name = "projects"
        self._client = None

    async def get_client(self) -> AsyncClient:
        """Get or create MeiliSearch client"""
        if self._client is None:
            self._client = AsyncClient(self.url, self.api_key)
        return self._client

    async def initialize(self):
        """Initialize MeiliSearch client and index"""
        client = await self.get_client()

        # Create index if it doesn't exist
        try:
            index = client.index(self.index_name)
            await index.get_stats()
        except Exception:
            # Index doesn't exist, create it
            await client.create_index(self.index_name, primary_key="id")

        # Configure the index
        await self.configure_index()

    async def index_project(self, project_data: Dict[str, Any]) -> bool:
        """Index a single project in MeiliSearch"""
        try:
            client = await self.get_client()
            index = client.index(self.index_name)
            await index.add_documents([project_data])
            return True
        except Exception:
            return False

    async def index_projects(self, projects: List[Dict[str, Any]]) -> bool:
        """Bulk index multiple projects"""
        if not projects:
            return True

        try:
            client = await self.get_client()
            index = client.index(self.index_name)
            await index.add_documents(projects)
            return True
        except Exception:
            return False

    async def search_projects(
        self,
        query: str,
        filters: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Search projects with optional filters"""
        try:
            client = await self.get_client()
            index = client.index(self.index_name)

            search_params = {
                "limit": limit,
                "offset": offset,
            }

            if filters:
                search_params["filter"] = filters

            result = await index.search(query, **search_params)

            return {
                "hits": result.hits,
                "total": getattr(result, "estimated_total_hits", len(result.hits)),
                "query": query,
                "limit": limit,
                "offset": offset,
                "processing_time_ms": getattr(result, "processing_time_ms", 0),
            }
        except Exception:
            return {
                "hits": [],
                "total": 0,
                "query": query,
                "limit": limit,
                "offset": offset,
            }

    async def get_search_stats(self) -> Dict[str, Any]:
        """Get search index statistics"""
        try:
            client = await self.get_client()
            index = client.index(self.index_name)
            stats = await index.get_stats()

            return {
                "total_documents": stats.number_of_documents,
                "is_indexing": stats.is_indexing,
                "last_update": getattr(stats, "updated_at", None),
            }
        except Exception:
            return {"total_documents": 0, "is_indexing": False, "last_update": None}

    async def configure_index(self):
        """Configure search index settings"""
        try:
            client = await self.get_client()
            index = client.index(self.index_name)

            searchable_attributes = [
                "name",
                "description",
                "category",
                "repository_name",
            ]

            filterable_attributes = [
                "github_language",
                "category",
                "repository_name",
                "github_stars",
                "repository_topics",  # New field for topic filtering
            ]

            sortable_attributes = ["github_stars", "created_at"]

            # Apply configuration
            await index.update_searchable_attributes(searchable_attributes)
            await index.update_filterable_attributes(filterable_attributes)
            await index.update_sortable_attributes(sortable_attributes)

        except Exception:
            pass

    async def clear_index(self):
        """Clear all documents from the index"""
        try:
            client = await self.get_client()
            index = client.index(self.index_name)
            await index.delete_all_documents()
            return True
        except Exception:
            return False


# Global search service instance
search_service = SearchService()
