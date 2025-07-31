from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from .repository import Repository


class ProjectBase(SQLModel):
    """Base model for Project with common fields"""

    name: str = Field(index=True)
    description: Optional[str] = None
    url: Optional[str] = None  # Primary project URL
    github_url: Optional[str] = None  # GitHub URL if available

    # Categorization within awesome list
    category: Optional[str] = Field(index=True)  # Section name in awesome list
    tags: Optional[str] = None  # Comma-separated tags for POC

    # GitHub metadata (enriched later)
    github_stars: Optional[int] = None
    github_forks: Optional[int] = None
    github_language: Optional[str] = Field(index=True)
    github_last_commit: Optional[datetime] = None
    github_created_at: Optional[datetime] = None

    # Quality scoring
    popularity_score: Optional[float] = (
        None  # Computed score based on stars, activity, etc.
    )

    # Original content for debugging/reprocessing
    raw_markdown: Optional[str] = None  # Original markdown line

    # Status tracking
    is_active: bool = True
    github_enriched: bool = False  # Whether GitHub data has been fetched


class Project(ProjectBase, table=True):
    """Project table model"""

    id: Optional[int] = Field(default=None, primary_key=True)
    repository_id: int = Field(foreign_key="repository.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    repository: Repository = Relationship(back_populates="projects")


class ProjectCreate(ProjectBase):
    """Model for creating projects"""

    repository_id: int


class ProjectRead(ProjectBase):
    """Model for reading projects"""

    id: int
    repository_id: int
    created_at: datetime
    updated_at: datetime
    repository_name: Optional[str] = None  # Can be joined


class ProjectUpdate(SQLModel):
    """Model for updating projects"""

    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    github_url: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    github_stars: Optional[int] = None
    github_forks: Optional[int] = None
    github_language: Optional[str] = None
    github_last_commit: Optional[datetime] = None
    github_created_at: Optional[datetime] = None
    popularity_score: Optional[float] = None
    is_active: Optional[bool] = None
    github_enriched: Optional[bool] = None


class ProjectSearch(SQLModel):
    """Model for search results with additional computed fields"""

    id: int
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    github_url: Optional[str] = None
    category: Optional[str] = None
    github_stars: Optional[int] = None
    github_language: Optional[str] = None
    popularity_score: Optional[float] = None
    repository_name: str
    repository_full_name: str
