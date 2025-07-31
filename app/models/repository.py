from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from .project import Project


class RepositoryBase(SQLModel):
    """Base model for Repository with common fields"""

    name: str = Field(index=True)  # e.g., "awesome-python"
    full_name: str = Field(unique=True, index=True)  # e.g., "vinta/awesome-python"
    description: Optional[str] = None
    homepage_url: Optional[str] = None
    github_url: str  # Full GitHub URL

    # GitHub metadata
    stars: Optional[int] = None
    forks: Optional[int] = None
    language: Optional[str] = None
    topics: Optional[str] = None  # JSON string for POC

    # Sync tracking
    is_active: bool = True
    last_synced_at: Optional[datetime] = None
    sync_error: Optional[str] = None


class Repository(RepositoryBase, table=True):
    """Repository table model"""

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    projects: List[Project] = Relationship(back_populates="repository")


class RepositoryCreate(RepositoryBase):
    """Model for creating repositories"""

    pass


class RepositoryRead(RepositoryBase):
    """Model for reading repositories"""

    id: int
    created_at: datetime
    updated_at: datetime
    project_count: Optional[int] = None  # Can be computed


class RepositoryUpdate(SQLModel):
    """Model for updating repositories"""

    description: Optional[str] = None
    homepage_url: Optional[str] = None
    stars: Optional[int] = None
    forks: Optional[int] = None
    language: Optional[str] = None
    topics: Optional[str] = None
    is_active: Optional[bool] = None
    last_synced_at: Optional[datetime] = None
    sync_error: Optional[str] = None
