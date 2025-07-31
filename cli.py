"""
AwesomeIndex CLI - Unified command-line interface
"""

import asyncio
import sys
import os
from pathlib import Path
import json
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from sqlmodel import Session, select
from app.database import engine
from app.models.repository import Repository
from app.models.project import Project
from app.internal.github import github_client
from app.internal.parser import markdown_parser
from app.internal.search import search_service


async def seed_repositories(backup_file: Optional[str] = None) -> None:
    """Seed database with awesome repositories"""
    if backup_file and Path(backup_file).exists():
        print(f"📥 Loading repositories from {backup_file}")
        with open(backup_file) as f:
            repos_data = json.load(f)

        with Session(engine) as session:
            for repo_data in repos_data:
                if session.exec(
                    select(Repository).where(
                        Repository.full_name == repo_data["full_name"]
                    )
                ).first():
                    continue

                repo = Repository(**repo_data)
                session.add(repo)
            session.commit()
        print(f"✅ Loaded {len(repos_data)} repositories")
        return

    print("🌱 Discovering awesome repositories from GitHub...")
    readme_content = await github_client.get_readme_content("sindresorhus/awesome")
    if not readme_content:
        print("❌ Failed to fetch sindresorhus/awesome README")
        return

    import re

    github_pattern = re.compile(
        r"\[([^\]]+)\]\((https://github\.com/[^/]+/[^/)]+)(?:/[^)]*)?\)", re.IGNORECASE
    )
    repo_urls = set()

    for match in github_pattern.finditer(readme_content):
        url = match.group(2).rstrip("/")
        if "awesome" in url.lower() and "sindresorhus/awesome" not in url.lower():
            repo_urls.add(url)

    github_repos = [markdown_parser.extract_github_repo_name(url) for url in repo_urls]
    github_repos = [name for name in github_repos if name]

    print(f"🔗 Found {len(github_repos)} repositories")

    saved_count = 0
    with Session(engine) as session:
        for full_name in github_repos:
            if session.exec(
                select(Repository).where(Repository.full_name == full_name)
            ).first():
                continue

            repo_data = await github_client.get_repository(full_name)
            if not repo_data:
                continue

            # Get additional metadata including topics
            metadata = await github_client.get_repository_metadata(full_name)
            topics_json = json.dumps(metadata.get("topics", [])) if metadata else None

            repo = Repository(
                name=repo_data["name"],
                full_name=repo_data["full_name"],
                description=repo_data.get("description"),
                github_url=repo_data["html_url"],
                stars=repo_data.get("stargazers_count"),
                github_topics=topics_json,
            )
            session.add(repo)
            session.commit()
            saved_count += 1
            print(f"✅ Saved {full_name}")
            await asyncio.sleep(0.4)  # Rate limiting

    print(f"🎉 Saved {saved_count} repositories")


async def parse_projects() -> None:
    """Parse projects from repositories and index them"""
    await search_service.initialize()

    with Session(engine) as session:
        repos = session.exec(select(Repository)).all()

        for repo in repos:
            print(f"Processing {repo.name}...")

            readme_content = await github_client.get_readme_content(repo.full_name)
            if not readme_content:
                continue

            parsed_projects = markdown_parser.parse_awesome_readme(readme_content)
            if not parsed_projects:
                continue

            # Clear existing projects
            for project in session.exec(
                select(Project).where(Project.repository_id == repo.id)
            ).all():
                session.delete(project)

            # Add new projects
            db_projects = []
            search_docs = []

            for parsed in parsed_projects:
                project = Project(
                    repository_id=repo.id,
                    name=parsed.name,
                    description=parsed.description,
                    url=parsed.url,
                    category=parsed.category,
                )

                # Enrich with GitHub metadata if it's a GitHub project
                if parsed.url and "github.com" in parsed.url:
                    github_repo_name = markdown_parser.extract_github_repo_name(
                        parsed.url
                    )
                    if github_repo_name:
                        try:
                            github_data = await github_client.get_repository(
                                github_repo_name
                            )
                            if github_data:
                                project.github_stars = github_data.get(
                                    "stargazers_count", 0
                                )
                                project.github_language = github_data.get(
                                    "language", ""
                                )
                                project.github_topics = json.dumps(
                                    github_data.get("topics", [])
                                )

                            await asyncio.sleep(0.2)
                        except Exception as e:
                            print(f"  ⚠️ Failed to enrich {parsed.name}: {e}")

                session.add(project)
                db_projects.append(project)

            session.commit()

            # Prepare search documents
            for project in db_projects:
                # Parse repository topics from JSON string
                repository_topics = []
                if repo.github_topics:
                    try:
                        repository_topics = json.loads(repo.github_topics)
                    except (json.JSONDecodeError, TypeError):
                        repository_topics = []

                # Parse project topics from JSON string
                project_topics = []
                if project.github_topics:
                    try:
                        project_topics = json.loads(project.github_topics)
                    except (json.JSONDecodeError, TypeError):
                        project_topics = []

                search_docs.append(
                    {
                        "id": project.id,
                        "name": project.name,
                        "description": project.description or "",
                        "url": project.url,
                        "github_url": project.url
                        if project.url and "github.com" in project.url
                        else None,
                        "category": project.category or "",
                        "github_stars": project.github_stars or 0,
                        "github_language": project.github_language or "",
                        "github_topics": project_topics,
                        "repository_id": repo.id,
                        "repository_name": repo.name,
                        "repository_topics": repository_topics,
                        "created_at": project.created_at.isoformat()
                        if project.created_at
                        else None,
                        "updated_at": project.updated_at.isoformat()
                        if project.updated_at
                        else None,
                    }
                )

            await search_service.index_projects(search_docs)
            print(f"✅ Indexed {len(db_projects)} projects")


async def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python cli.py <command> [args]")
        print("Commands:")
        print("  seed [backup.json]  - Seed repositories")
        print("  parse [limit]       - Parse projects from repositories")
        print("  test               - Test search functionality")
        return

    command = sys.argv[1]

    try:
        if command == "seed":
            backup_file = sys.argv[2] if len(sys.argv) > 2 else None
            await seed_repositories(backup_file)
        elif command == "parse":
            await parse_projects()
        else:
            print(f"Unknown command: {command}")
    finally:
        await github_client.close()


if __name__ == "__main__":
    asyncio.run(main())
