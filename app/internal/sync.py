from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select
from app.database import get_session
from app.models import Repository, Project
from .github import github_client
from .parser import markdown_parser
from .search import search_service


class SyncService:
    """Service for synchronizing data from GitHub to local database"""

    async def discover_awesome_repositories(self, limit: int = 50) -> List[dict]:
        """Discover awesome repositories from GitHub"""
        repos = await github_client.search_awesome_repositories(limit)

        # Filter for actual awesome lists (basic heuristics)
        filtered_repos = []
        for repo in repos:
            name = repo.get("name", "").lower()
            description = repo.get("description", "").lower()

            # Basic filtering for awesome lists
            if (
                name.startswith("awesome-")
                or "awesome" in description
                and ("list" in description or "collection" in description)
            ):
                filtered_repos.append(repo)

        return filtered_repos

    async def sync_repository(self, github_full_name: str) -> Optional[Repository]:
        """Sync a single repository and its projects"""
        # Get repository data from GitHub
        repo_data = await github_client.get_repository(github_full_name)
        if not repo_data:
            return None

        # Get or create repository in database
        with next(get_session()) as session:
            repository = self._upsert_repository(session, repo_data)

            # Get README content and parse projects
            readme_content = await github_client.get_readme_content(github_full_name)
            if readme_content:
                projects = await self._sync_repository_projects(
                    session, repository, readme_content
                )

                # Update sync status
                repository.last_synced_at = datetime.utcnow()
                repository.sync_error = None
                session.add(repository)
                session.commit()

                # Index projects in search
                await self._index_projects_for_search(projects)

                return repository

            # Mark sync error if no README
            repository.sync_error = "Could not fetch README content"
            repository.last_synced_at = datetime.utcnow()
            session.add(repository)
            session.commit()

            return repository

    def _upsert_repository(self, session: Session, repo_data: dict) -> Repository:
        """Create or update repository from GitHub data"""
        full_name = repo_data["full_name"]

        # Check if repository exists
        statement = select(Repository).where(Repository.full_name == full_name)
        existing_repo = session.exec(statement).first()

        if existing_repo:
            # Update existing repository
            existing_repo.name = repo_data["name"]
            existing_repo.description = repo_data.get("description")
            existing_repo.stars = repo_data.get("stargazers_count")
            existing_repo.language = repo_data.get("language")
            existing_repo.updated_at = datetime.utcnow()
            session.add(existing_repo)
            return existing_repo
        else:
            # Create new repository
            new_repo = Repository(
                name=repo_data["name"],
                full_name=full_name,
                description=repo_data.get("description"),
                github_url=repo_data["html_url"],
                stars=repo_data.get("stargazers_count"),
                language=repo_data.get("language"),
            )
            session.add(new_repo)
            session.flush()  # Get the ID
            return new_repo

    async def _sync_repository_projects(
        self, session: Session, repository: Repository, readme_content: str
    ) -> List[Project]:
        """Parse README and sync projects for a repository"""
        # Parse projects from README
        parsed_projects = markdown_parser.parse_awesome_readme(readme_content)

        # Clear existing projects for this repository
        statement = select(Project).where(Project.repository_id == repository.id)
        existing_projects = session.exec(statement).all()
        for project in existing_projects:
            session.delete(project)

        # Create new projects
        new_projects = []
        for parsed_project in parsed_projects:
            project = Project(
                repository_id=repository.id,
                name=parsed_project.name,
                description=parsed_project.description,
                url=parsed_project.url,
                github_url=parsed_project.github_url,
                category=parsed_project.category,
            )
            session.add(project)
            new_projects.append(project)

        session.commit()
        return new_projects

    async def _index_projects_for_search(self, projects: List[Project]):
        """Index projects in MeiliSearch"""
        if not projects:
            return

        # Convert projects to search documents
        search_docs = []
        for project in projects:
            doc = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "url": project.url,
                "github_url": project.github_url,
                "category": project.category,
                "github_language": project.github_language,
                "github_stars": project.github_stars,
                "repository_id": project.repository_id,
                "repository_name": project.repository.name
                if project.repository
                else None,
            }
            search_docs.append(doc)

        # Index in MeiliSearch
        await search_service.index_projects(search_docs)

    async def sync_all_discovered_repositories(self, limit: int = 10) -> dict:
        """Discover and sync multiple repositories"""
        discovered_repos = await self.discover_awesome_repositories(limit * 2)

        results = {
            "discovered": len(discovered_repos),
            "synced": 0,
            "errors": 0,
            "repositories": [],
        }

        # Sync first `limit` repositories
        for repo_data in discovered_repos[:limit]:
            try:
                repository = await self.sync_repository(repo_data["full_name"])
                if repository:
                    results["synced"] += 1
                    results["repositories"].append(
                        {
                            "full_name": repository.full_name,
                            "status": "synced",
                            "projects_count": len(repository.projects)
                            if repository.projects
                            else 0,
                        }
                    )
                else:
                    results["errors"] += 1
                    results["repositories"].append(
                        {
                            "full_name": repo_data["full_name"],
                            "status": "error",
                            "error": "Could not sync repository",
                        }
                    )
            except Exception as e:
                results["errors"] += 1
                results["repositories"].append(
                    {
                        "full_name": repo_data["full_name"],
                        "status": "error",
                        "error": str(e),
                    }
                )

        return results


# Global sync service instance
sync_service = SyncService()
