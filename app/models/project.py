from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .repository import Repository


class Project(SQLModel, table=True):
    """Project model"""

    id: Optional[int] = Field(default=None, primary_key=True)
    repository_id: int = Field(foreign_key="repository.id", index=True)

    name: str = Field(index=True)
    description: Optional[str] = None
    url: Optional[str] = None
    github_url: Optional[str] = None
    category: Optional[str] = Field(default=None, index=True)

    # GitHub metadata
    github_stars: Optional[int] = None
    github_language: Optional[str] = Field(default=None, index=True)
    readme_excerpt: Optional[str] = None  # First ~200 chars of README

    # Status
    is_active: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    repository: "Repository" = Relationship(back_populates="projects")
