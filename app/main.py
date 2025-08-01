from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import json

from app.config import settings
from app.database import create_db_and_tables
from app.routers import search, projects
from app.internal.search import search_service
from sqlmodel import Session, select
from sqlalchemy import func
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
    # Fetch initial browse results to avoid flicker
    with Session(engine) as session:
        # Get top 50 projects sorted by stars
        statement = (
            select(Project).order_by(Project.github_stars.desc()).offset(0).limit(50)
        )
        projects = session.exec(statement).all()

        # Get total count
        total_count = session.exec(select(func.count(Project.id))).one()

        # Convert to search result format
        hits = []
        for project in projects:
            repo = session.get(Repository, project.repository_id)
            topics = []
            if project.github_topics:
                try:
                    topics = json.loads(project.github_topics)
                except:
                    pass

            hits.append(
                {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "url": project.url,
                    "category": project.category,
                    "github_stars": project.github_stars,
                    "github_language": project.github_language,
                    "github_topics": topics,
                    "repository_name": repo.name if repo else "",
                    "repository_url": repo.github_url if repo else "",
                }
            )

        initial_results = {
            "hits": hits,
            "total": total_count,
            "offset": 0,
            "has_more": total_count > 50,
        }
        
        # Get filter options for server-side rendering
        # Get unique languages
        lang_statement = select(Project.github_language).distinct().where(Project.github_language != None)
        languages = [lang for lang in session.exec(lang_statement) if lang]
        languages.sort()
        
        # Get unique categories
        cat_statement = select(Project.category).distinct().where(Project.category != None)
        categories = [cat for cat in session.exec(cat_statement) if cat]
        categories.sort()
        
        # Get repositories that have projects
        repo_statement = (
            select(Repository.name)
            .join(Project, Repository.id == Project.repository_id)
            .distinct()
            .order_by(Repository.name)
        )
        repositories = list(session.exec(repo_statement))

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "initial_results": initial_results,
                "query": "",
                "next_offset": 50,
                "filters": {
                    "sort": "stars",
                    "repository": "",
                    "language": "",
                    "category": "",
                    "min_stars": 0,
                },
                "filter_options": {
                    "languages": languages,
                    "categories": categories,
                    "repositories": repositories,
                    "total_projects": total_count,
                },
            },
        )


@app.get("/results")
async def get_results(
    request: Request,
    q: str = "",
    category: str = "",
    repository: str = "",
    sort: str = "stars",
    language: str = "",
    min_stars: int = 0,
    limit: int = 50,
    offset: int = 0,
):
    """Unified endpoint for both search and browse functionality"""
    
    # If there's a query, use MeiliSearch
    if q:
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
                limit=limit + 1,  # Get one extra to check if there are more
                offset=offset,
            )

            # Check if there are more results
            has_more = len(results["hits"]) > limit
            results["hits"] = results["hits"][:limit]
            results["has_more"] = has_more

            # Enrich hits with repository URLs if missing
            with Session(engine) as session:
                for hit in results["hits"]:
                    if "repository_url" not in hit and "repository_id" in hit:
                        repo = session.exec(
                            select(Repository).where(
                                Repository.id == hit["repository_id"]
                            )
                        ).first()
                        if repo:
                            hit["repository_url"] = repo.github_url
        except Exception as e:
            results = {"hits": [], "total": 0, "has_more": False, "error": str(e)}
    else:
        # Browse mode - use database directly
        with Session(engine) as session:
            statement = select(Project)

            # Apply filters
            if repository:
                # Get repository by name
                repo = session.exec(
                    select(Repository).where(Repository.name == repository)
                ).first()
                if repo:
                    statement = statement.where(Project.repository_id == repo.id)
            if category:
                statement = statement.where(Project.category == category)
            if language:
                statement = statement.where(Project.github_language == language)
            if min_stars > 0:
                statement = statement.where(Project.github_stars >= min_stars)

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

                # Parse topics from JSON
                topics = []
                if project.github_topics:
                    try:
                        topics = json.loads(project.github_topics)
                    except:
                        pass

                hits.append(
                    {
                        "id": project.id,
                        "name": project.name,
                        "description": project.description,
                        "url": project.url,
                        "category": project.category,
                        "github_stars": project.github_stars,
                        "github_language": project.github_language,
                        "github_topics": topics,
                        "repository_name": repo.name if repo else "",
                        "repository_url": repo.github_url if repo else "",
                    }
                )

            # Get total count for display
            count_statement = select(func.count(Project.id))
            if repository:
                repo = session.exec(
                    select(Repository).where(Repository.name == repository)
                ).first()
                if repo:
                    count_statement = count_statement.where(
                        Project.repository_id == repo.id
                    )
            if category:
                count_statement = count_statement.where(Project.category == category)
            if language:
                count_statement = count_statement.where(Project.github_language == language)
            if min_stars > 0:
                count_statement = count_statement.where(Project.github_stars >= min_stars)

            total_count = session.exec(count_statement).one()

            results = {
                "hits": hits,
                "total": total_count,
                "offset": offset,
                "has_more": has_more,
            }

    # Use different template for infinite scroll continuation
    template_name = "results_more.html" if offset > 0 else "results.html"

    return templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "results": results,
            "query": q,
            "next_offset": offset + limit,
            "filters": {
                "sort": sort,
                "repository": repository,
                "language": language,
                "category": category,
                "min_stars": min_stars,
            },
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
