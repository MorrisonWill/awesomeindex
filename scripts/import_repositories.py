"""
Import repositories from JSON backup file to database.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to Python path and change working directory FIRST
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from sqlmodel import Session, select

from app.database import engine, create_db_and_tables
from app.models.repository import Repository


def import_repositories_from_json(input_file: str, overwrite: bool = False) -> None:
    """Import repositories from a JSON backup file"""
    print("📥 Starting repository import...")

    # Check if file exists
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return

    # Ensure database tables exist
    create_db_and_tables()

    # Load JSON data
    with open(input_file, "r", encoding="utf-8") as f:
        backup_data = json.load(f)

    repositories_data = backup_data.get("repositories", [])
    export_timestamp = backup_data.get("export_timestamp", "unknown")
    total_count = backup_data.get("total_repositories", len(repositories_data))

    print(f"📊 Backup contains {total_count} repositories")
    print(f"📅 Export timestamp: {export_timestamp}")

    imported_count = 0
    skipped_count = 0
    updated_count = 0

    with Session(engine) as session:
        for repo_data in repositories_data:
            try:
                # Check if repository already exists
                existing = session.exec(
                    select(Repository).where(
                        Repository.full_name == repo_data["full_name"]
                    )
                ).first()

                if existing:
                    if overwrite:
                        # Update existing repository
                        existing.name = repo_data["name"]
                        existing.description = repo_data.get("description")
                        existing.github_url = repo_data["github_url"]
                        existing.stars = repo_data.get("stars")
                        existing.language = repo_data.get("language")
                        existing.is_active = repo_data.get("is_active", True)
                        existing.sync_error = repo_data.get("sync_error")
                        existing.updated_at = datetime.utcnow()

                        # Parse timestamps if provided
                        if repo_data.get("last_synced_at"):
                            existing.last_synced_at = datetime.fromisoformat(
                                repo_data["last_synced_at"]
                            )

                        session.add(existing)
                        updated_count += 1
                        print(f"🔄 Updated {repo_data['full_name']}")
                    else:
                        skipped_count += 1
                        print(f"⏭️  Skipping {repo_data['full_name']} (already exists)")
                        continue
                else:
                    # Create new repository
                    repository = Repository(
                        name=repo_data["name"],
                        full_name=repo_data["full_name"],
                        description=repo_data.get("description"),
                        github_url=repo_data["github_url"],
                        stars=repo_data.get("stars"),
                        language=repo_data.get("language"),
                        is_active=repo_data.get("is_active", True),
                        sync_error=repo_data.get("sync_error"),
                        created_at=datetime.fromisoformat(repo_data["created_at"])
                        if repo_data.get("created_at")
                        else datetime.utcnow(),
                        updated_at=datetime.fromisoformat(repo_data["updated_at"])
                        if repo_data.get("updated_at")
                        else datetime.utcnow(),
                    )

                    # Parse last_synced_at if provided
                    if repo_data.get("last_synced_at"):
                        repository.last_synced_at = datetime.fromisoformat(
                            repo_data["last_synced_at"]
                        )

                    session.add(repository)
                    imported_count += 1
                    print(f"✅ Imported {repo_data['full_name']}")

                # Commit every 10 repositories to avoid large transactions
                if (imported_count + updated_count) % 10 == 0:
                    session.commit()

            except Exception as e:
                print(
                    f"❌ Error importing {repo_data.get('full_name', 'unknown')}: {e}"
                )
                session.rollback()
                continue

        # Final commit
        session.commit()

    print(f"\n🎉 Import complete!")
    print(f"📈 Imported: {imported_count} new repositories")
    print(f"🔄 Updated: {updated_count} existing repositories")
    print(f"⏭️  Skipped: {skipped_count} existing repositories")
    print(f"📊 Total processed: {imported_count + updated_count + skipped_count}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import repositories from JSON backup")
    parser.add_argument("input_file", help="Input JSON backup file path")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing repositories (default: skip existing)",
    )

    args = parser.parse_args()
    import_repositories_from_json(args.input_file, args.overwrite)
