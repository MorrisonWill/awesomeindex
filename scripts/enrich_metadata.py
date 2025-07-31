#!/usr/bin/env python3
"""
Script to populate empty GitHub metadata for projects and repositories.
Fixes the broken github_stars and github_language columns.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from app.database import engine
from app.models.project import Project
from app.models.repository import Repository
from app.internal.github import github_client
from app.internal.parser import markdown_parser


async def enrich_project_metadata(session: Session, project: Project) -> bool:
    """Enrich a single project with GitHub metadata"""
    if not project.github_url:
        return False

    # Extract repo name from GitHub URL
    repo_name = markdown_parser.extract_github_repo_name(project.github_url)
    if not repo_name:
        print(f"Could not extract repo name from: {project.github_url}")
        return False

    print(f"Enriching project: {project.name} ({repo_name})")

    try:
        # Get repository metadata
        metadata = await github_client.get_repository_metadata(repo_name)
        if not metadata:
            print(f"  Failed to get metadata for {repo_name}")
            return False

        # Get README excerpt
        readme_excerpt = await github_client.get_readme_excerpt(repo_name, 200)

        # Update project
        project.github_stars = metadata.get("stars", 0)
        project.github_language = metadata.get("language")
        project.readme_excerpt = readme_excerpt

        session.add(project)
        print(
            f"  ✓ Updated: {metadata.get('stars', 0)} stars, {metadata.get('language', 'N/A')} language"
        )
        return True

    except Exception as e:
        print(f"  Error enriching {repo_name}: {e}")
        return False


async def enrich_repository_metadata(session: Session, repository: Repository) -> bool:
    """Enrich a single repository with GitHub metadata"""
    # Extract repo name from GitHub URL
    repo_name = repository.full_name

    print(f"Enriching repository: {repository.name} ({repo_name})")

    try:
        # Get repository metadata
        metadata = await github_client.get_repository_metadata(repo_name)
        if not metadata:
            print(f"  Failed to get metadata for {repo_name}")
            return False

        # Update repository
        repository.github_topics = json.dumps(metadata.get("topics", []))

        session.add(repository)
        print(f"  ✓ Updated: {len(metadata.get('topics', []))} topics")
        return True

    except Exception as e:
        print(f"  Error enriching {repo_name}: {e}")
        return False


async def main():
    """Main enrichment function"""
    print("Starting GitHub metadata enrichment...")

    with Session(engine) as session:
        # Get projects that need enrichment (have GitHub URL but no stars)
        projects_to_enrich = session.exec(
            select(Project).where(
                Project.github_url.is_not(None), Project.github_stars.is_(None)
            )
        ).all()

        print(f"Found {len(projects_to_enrich)} projects to enrich")

        # Get repositories that need topic enrichment
        repositories_to_enrich = session.exec(
            select(Repository).where(Repository.github_topics.is_(None))
        ).all()

        print(f"Found {len(repositories_to_enrich)} repositories to enrich")

        # Enrich projects
        project_success_count = 0
        for i, project in enumerate(projects_to_enrich, 1):
            print(f"\n[{i}/{len(projects_to_enrich)}] Processing project...")
            if await enrich_project_metadata(session, project):
                project_success_count += 1

            # Commit every 10 projects to avoid losing progress
            if i % 10 == 0:
                session.commit()
                print(f"  Committed progress ({i} projects processed)")

        # Enrich repositories
        repo_success_count = 0
        for i, repository in enumerate(repositories_to_enrich, 1):
            print(f"\n[{i}/{len(repositories_to_enrich)}] Processing repository...")
            if await enrich_repository_metadata(session, repository):
                repo_success_count += 1

        # Final commit
        session.commit()

        print(f"\n✅ Enrichment complete!")
        print(f"Projects enriched: {project_success_count}/{len(projects_to_enrich)}")
        print(
            f"Repositories enriched: {repo_success_count}/{len(repositories_to_enrich)}"
        )

    await github_client.close()


if __name__ == "__main__":
    asyncio.run(main())
