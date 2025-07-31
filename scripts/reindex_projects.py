#!/usr/bin/env python3
"""
Script to re-index all projects in MeiliSearch with updated metadata.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from app.database import engine
from app.models.project import Project
from app.models.repository import Repository
from app.internal.search import search_service


def project_to_search_document(
    project: Project, repository: Repository
) -> Dict[str, Any]:
    """Convert a project and repository to a search document"""
    # Parse repository topics from JSON string
    repository_topics = []
    if repository.github_topics:
        try:
            repository_topics = json.loads(repository.github_topics)
        except (json.JSONDecodeError, TypeError):
            repository_topics = []

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description or "",
        "url": project.url,
        "github_url": project.github_url,
        "category": project.category or "",
        "github_stars": project.github_stars or 0,
        "github_language": project.github_language or "",
        "readme_excerpt": project.readme_excerpt or "",
        "repository_id": project.repository_id,
        "repository_name": repository.name,
        "repository_topics": repository_topics,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


async def main():
    """Main re-indexing function"""
    print("Starting MeiliSearch re-indexing...")

    # Initialize search service
    await search_service.initialize()

    # Clear existing index
    print("Clearing existing search index...")
    await search_service.clear_index()

    with Session(engine) as session:
        # Get all projects with their repositories
        projects_with_repos = session.exec(
            select(Project, Repository)
            .join(Repository, Project.repository_id == Repository.id)
            .where(Project.is_active == True)
        ).all()

        print(f"Found {len(projects_with_repos)} active projects to index")

        # Convert to search documents
        documents = []
        for project, repository in projects_with_repos:
            doc = project_to_search_document(project, repository)
            documents.append(doc)

        # Batch index documents
        batch_size = 100
        total_indexed = 0

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]

            print(f"Indexing batch {i // batch_size + 1} ({len(batch)} documents)")
            success = await search_service.index_projects(batch)

            if success:
                total_indexed += len(batch)
                print(f"  ✓ Indexed {len(batch)} documents")
            else:
                print(f"  ✗ Failed to index batch")

        print(f"\n✅ Re-indexing complete!")
        print(f"Total documents indexed: {total_indexed}/{len(documents)}")

        # Get final stats
        stats = await search_service.get_search_stats()
        print(f"Search index now contains: {stats['total_documents']} documents")


if __name__ == "__main__":
    asyncio.run(main())
