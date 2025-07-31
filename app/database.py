from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from app.config import settings

# Import models to register them with SQLModel
from app.models import Repository, Project

engine = create_engine(settings.database_url, echo=settings.debug)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
