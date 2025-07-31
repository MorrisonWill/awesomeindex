from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .project import Project


class Repository(SQLModel, table=True):
    """Repository model"""

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(index=True)
    full_name: str = Field(unique=True, index=True)
    description: Optional[str] = None
    github_url: str

    # GitHub metadata
    stars: Optional[int] = None

    # Sync tracking
    is_active: bool = True
    last_synced_at: Optional[datetime] = None
    sync_error: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    projects: List["Project"] = Relationship(back_populates="repository")
