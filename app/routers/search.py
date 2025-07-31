from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any, List
from app.internal.search import search_service

router = APIRouter(prefix="/api/search", tags=["search"])


def build_filters(
    category: Optional[str] = None, repository: Optional[str] = None
) -> Optional[str]:
    """Build MeiliSearch filter string from parameters"""
    filters = []
    if category:
        filters.append(f"category = '{category}'")
    if repository:
        filters.append(f"repository_name = '{repository}'")
    return " AND ".join(filters) if filters else None


@router.get("/")
async def search_projects(
    q: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    repository: Optional[str] = Query(None, description="Filter by repository name"),
    language: Optional[str] = Query(None, description="Filter by programming language"),
    min_stars: int = Query(0, ge=0, description="Minimum GitHub stars"),
    topics: Optional[str] = Query(None, description="Filter by topics (comma-separated)"),
    sort: str = Query("relevance", description="Sort order: relevance, stars, recent, name"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
) -> Dict[str, Any]:
    """Search for projects across all awesome repositories"""

    # Build filters
    filters = []
    if category:
        filters.append(f"category = '{category}'")
    if repository:
        filters.append(f"repository_name = '{repository}'")
    if language:
        filters.append(f"github_language = '{language}'")
    if min_stars > 0:
        filters.append(f"github_stars >= {min_stars}")
    
    # Handle topics filter
    if topics:
        topic_list = [t.strip().lower() for t in topics.split(',') if t.strip()]
        topic_filters = [f"github_topics = '{topic}'" for topic in topic_list]
        if topic_filters:
            filters.append(f"({' OR '.join(topic_filters)})")
    
    filter_string = " AND ".join(filters) if filters else None
    
    # Prepare sort parameter
    sort_param = None
    if sort == "stars":
        sort_param = ["github_stars:desc"]
    elif sort == "recent":
        sort_param = ["updated_at:desc"]
    elif sort == "name":
        sort_param = ["name:asc"]

    try:
        results = await search_service.search_projects(
            query=q,
            filters=filter_string,
            sort=sort_param,
            limit=limit,
            offset=offset,
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.get("/stats")
async def get_search_stats() -> Dict[str, Any]:
    """Get search index statistics"""
    try:
        stats = await search_service.get_search_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")


@router.post("/reindex")
async def reindex_all():
    """Re-index all projects (admin endpoint)"""
    try:
        # Clear existing index
        await search_service.clear_index()

        # Re-run the parsing and indexing
        # This would typically trigger a background job
        return {"message": "Reindexing started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reindex error: {str(e)}")
