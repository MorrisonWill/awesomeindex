from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List, Optional
from app.database import engine, get_session
from app.models.project import Project
from app.models.repository import Repository

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/", response_model=List[Project])
async def list_projects(
    repository_id: Optional[int] = None,
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    session: Session = Depends(get_session),
):
    """List projects with optional filtering"""

    statement = select(Project)

    if repository_id:
        statement = statement.where(Project.repository_id == repository_id)

    if category:
        statement = statement.where(Project.category == category)

    statement = statement.offset(offset).limit(limit)

    projects = session.exec(statement).all()
    return projects


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: int, session: Session = Depends(get_session)):
    """Get a specific project by ID"""

    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.get("/repository/{repository_id}", response_model=List[Project])
async def get_projects_by_repository(
    repository_id: int,
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_session),
):
    """Get all projects from a specific repository"""

    # Verify repository exists
    repository = session.get(Repository, repository_id)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    statement = (
        select(Project)
        .where(Project.repository_id == repository_id)
        .offset(offset)
        .limit(limit)
    )

    projects = session.exec(statement).all()
    return projects


@router.get("/categories/")
async def list_categories(session: Session = Depends(get_session)):
    """Get all unique categories"""

    statement = select(Project.category).distinct().where(Project.category.is_not(None))
    categories = session.exec(statement).all()

    return {"categories": sorted([cat for cat in categories if cat])}


@router.get("/repositories/")
async def list_repositories_with_projects(session: Session = Depends(get_session)):
    """Get all repositories that have projects"""

    statement = select(Repository).join(Project).distinct()

    repositories = session.exec(statement).all()
    return repositories
