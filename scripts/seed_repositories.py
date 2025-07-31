"""
Seed script to populate the database with awesome repositories.
Scrapes https://github.com/sindresorhus/awesome for repository links.
"""

import asyncio
import os
import sys
import re
from datetime import datetime
from typing import List
from pathlib import Path

# Add the project root to Python path and change working directory FIRST
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from sqlmodel import Session, select

from app.database import engine
from app.internal.github import github_client
from app.internal.parser import markdown_parser
from app.models.repository import Repository


class AwesomeRepositorySeeder:
    """Seeds database with awesome repositories from sindresorhus/awesome"""

    def __init__(self):
        self.github_client = github_client
        self.parser = markdown_parser

    async def seed_repositories(self) -> None:
        """Main seeding function"""
        print("🌱 Starting repository seeding...")

        # Get the awesome-awesome README content
        print("📥 Fetching sindresorhus/awesome README...")
        readme_content = await self.github_client.get_readme_content(
            "sindresorhus/awesome"
        )

        print("readme content", readme_content)

        if not readme_content:
            print("❌ Failed to fetch README content")
            return

        print("✅ README content fetched successfully")

        # Extract repository URLs from the README
        print("🔍 Extracting repository URLs...")
        repo_urls = self._extract_awesome_repositories(readme_content)
        print(f"📊 Found {len(repo_urls)} potential awesome repositories")

        # Filter to only GitHub repositories and extract full names
        github_repos = []
        for url in repo_urls:
            full_name = self.parser.extract_github_repo_name(url)
            if full_name and full_name not in [repo[1] for repo in github_repos]:
                github_repos.append((url, full_name))

        print(f"🔗 Filtered to {len(github_repos)} GitHub repositories")

        # Fetch repository metadata and save to database
        print("💾 Fetching repository metadata and saving to database...")
        saved_count = 0

        with Session(engine) as session:
            for i, (url, full_name) in enumerate(github_repos):
                try:
                    print(f"[{i + 1}/10] Processing {full_name}")

                    # Check if repository already exists
                    existing = session.exec(
                        select(Repository).where(Repository.full_name == full_name)
                    ).first()

                    if existing:
                        print(f"⏭️  Skipping {full_name} (already exists)")
                        continue

                    # Fetch repository metadata from GitHub API
                    repo_data = await self.github_client.get_repository(full_name)

                    if not repo_data:
                        print(f"⚠️  Could not fetch metadata for {full_name}")
                        continue

                    # Create repository record
                    repository = Repository(
                        name=repo_data["name"],
                        full_name=repo_data["full_name"],
                        description=repo_data.get("description"),
                        github_url=repo_data["html_url"],
                        stars=repo_data.get("stargazers_count"),
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )

                    session.add(repository)
                    session.commit()
                    saved_count += 1

                    print(
                        f"✅ Saved {full_name} ({repo_data.get('stargazers_count', 0)} stars)"
                    )

                    # Rate limiting - be nice to GitHub API
                    await asyncio.sleep(0.4)

                except Exception as e:
                    print(f"❌ Error processing {full_name}: {e}")
                    session.rollback()
                    continue

        print(f"🎉 Seeding complete! Saved {saved_count} repositories to database")

    def _extract_awesome_repositories(self, content: str) -> List[str]:
        """Extract GitHub repository URLs from the awesome-awesome README"""
        urls = set()

        # Pattern to match GitHub repository URLs in markdown links
        # Matches: [text](https://github.com/owner/repo)
        github_pattern = re.compile(
            r"\[([^\]]+)\]\((https://github\.com/[^/]+/[^/)]+)(?:/[^)]*)?\)",
            re.IGNORECASE,
        )

        for match in github_pattern.finditer(content):
            url = match.group(2)
            # Clean up URL (remove trailing slashes, fragments, etc.)
            url = url.rstrip("/")

            # Only include if it looks like an awesome repository
            if self._is_likely_awesome_repo(url, match.group(1)):
                urls.add(url)

        return list(urls)

    def _is_likely_awesome_repo(self, url: str, link_text: str) -> bool:
        """Check if URL/text suggests this is an awesome repository"""
        url_lower = url.lower()
        text_lower = link_text.lower()

        # Must contain "awesome" in URL or link text
        if "awesome" not in url_lower and "awesome" not in text_lower:
            return False

        # Exclude some common non-repo URLs
        excludes = [
            "github.com/sindresorhus/awesome",  # The main awesome repo itself
            "/issues",
            "/pulls",
            "/wiki",
            "/blob/",
            "/tree/",
        ]

        for exclude in excludes:
            if exclude in url_lower:
                return False

        return True


async def main():
    """Run the seeding script"""
    seeder = AwesomeRepositorySeeder()
    try:
        await seeder.seed_repositories()
    finally:
        await github_client.close()


if __name__ == "__main__":
    asyncio.run(main())
