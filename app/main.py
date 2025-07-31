from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from app.config import settings
from app.database import create_db_and_tables
from app.routers import search, projects
from app.internal.search import search_service
from sqlmodel import Session, select
from app.database import engine, get_session
from app.models.project import Project
from app.models.repository import Repository


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    await search_service.initialize()
    yield
    # Shutdown
    pass


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

# Static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(search.router)
app.include_router(projects.router)


@app.get("/")
async def homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/browse")
async def browse_projects(
    request: Request,
    offset: int = 0,
    limit: int = 20,
    sort: str = "stars",
    repository: str = "",
    language: str = "",
    category: str = "",
    min_stars: int = 0,
    topics: str = "",
):
    """Browse all projects with infinite scroll"""
    with Session(engine) as session:
        statement = select(Project)
        
        # Apply filters
        if repository:
            # Get repository by name
            repo = session.exec(select(Repository).where(Repository.name == repository)).first()
            if repo:
                statement = statement.where(Project.repository_id == repo.id)
        if category:
            statement = statement.where(Project.category == category)
        if language:
            statement = statement.where(Project.github_language == language)
        if min_stars > 0:
            statement = statement.where(Project.github_stars >= min_stars)
        if topics:
            # Filter by topics (comma-separated)
            topic_list = [t.strip().lower() for t in topics.split(',') if t.strip()]
            for topic in topic_list:
                statement = statement.where(
                    Project.github_topics.contains(f'"{topic}"')
                )
            
        # Apply sorting
        if sort == "stars":
            statement = statement.order_by(Project.github_stars.desc())
        elif sort == "recent":
            statement = statement.order_by(Project.updated_at.desc())
        elif sort == "name":
            statement = statement.order_by(Project.name)
            
        statement = statement.offset(offset).limit(limit + 1)
        projects = session.exec(statement).all()
        
        has_more = len(projects) > limit
        projects = projects[:limit]
        
        # Convert to search result format for reuse of template
        hits = []
        for project in projects:
            # Get repository name
            repo = session.get(Repository, project.repository_id)
            hits.append({
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "url": project.url,
                "category": project.category,
                "github_stars": project.github_stars,
                "github_language": project.github_language,
                "repository_name": repo.name if repo else "",
            })
        
        results = {
            "hits": hits,
            "total": len(hits),
            "offset": offset,
            "has_more": has_more,
        }
        
        return templates.TemplateResponse(
            "browse_results.html", 
            {
                "request": request, 
                "results": results, 
                "next_offset": offset + limit,
                "filters": {
                    "sort": sort,
                    "repository": repository,
                    "language": language,
                    "category": category,
                    "min_stars": min_stars,
                    "topics": topics,
                }
            }
        )


@app.get("/search")
async def search_frontend(
    request: Request,
    q: str,
    category: str = "",
    repository: str = "",
    sort: str = "relevance",
    language: str = "",
    min_stars: int = 0,
    topics: str = "",
    limit: int = 20,
):
    """Frontend search endpoint that returns HTML"""
    from app.routers.search import build_filters
    
    # Build filter string for MeiliSearch
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
    
    # Prepare sort parameter for MeiliSearch
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
            offset=0,
        )
        
        return templates.TemplateResponse(
            "search_results.html", 
            {"request": request, "results": results}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "search_results.html",
            {"request": request, "results": {"hits": [], "total": 0}, "error": str(e)}
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
