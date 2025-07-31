from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from app.config import settings
from app.database import create_db_and_tables
from app.routers import search, projects
from app.internal.search import search_service
from sqlmodel import Session, select
from app.database import engine
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


@app.get("/search")
async def search_frontend(
    request: Request,
    q: str,
    category: str = "",
    repository: str = "",
    limit: int = 20,
):
    """Frontend search endpoint that returns HTML"""
    from app.routers.search import build_filters
    
    filter_string = build_filters(category, repository)
    
    try:
        results = await search_service.search_projects(
            query=q,
            filters=filter_string,
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
