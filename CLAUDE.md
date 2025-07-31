# CLAUDE.md

## Project Overview

**AwesomeIndex** is a search engine for individual projects within GitHub's "Awesome" repositories. Unlike existing solutions that only search repository names and descriptions, AwesomeIndex indexes and searches the actual project entries within these curated lists.

## Problem Statement

GitHub's "Awesome" repositories (like `awesome-python`, `awesome-javascript`) contain thousands of curated projects, but there's no way to search for specific projects across all these lists. Developers must manually browse through massive markdown files to find relevant tools and libraries.

## Solution

A web platform that:
- Discovers and monitors Awesome repositories via GitHub API
- Parses markdown content to extract individual project entries
- Indexes projects in MeiliSearch for instant, typo-tolerant search
- Provides a fast, SEO-friendly web interface for discovery

## Technology Stack

### Backend
- **Python 3.12+** - Main language
- **FastAPI** - Web framework
- **SQLModel** - Database ORM with type safety
- **SQLite** - Database (with WAL mode for performance)
- **MeiliSearch** - Search engine (meilisearch-python-sdk)
- **httpx** - HTTP client for API calls
- **uv** - Package management
- **ruff** - Linting and formatting
- **ty** - Type checking (Astral's type checker)

### Frontend
- **HTMX** - Dynamic interactions without JavaScript frameworks
- **Alpine.js** - Minimal JavaScript for UI components
- **Jinja2** - Server-side templating
- **CSS** - Custom responsive styling

### External APIs
- **GitHub API** - Repository discovery and metadata
- **MeiliSearch** - Search indexing and queries

## Project Structure

```
awesomeindex/
├── app/
│   ├── main.py              # FastAPI application entry
│   ├── config.py            # Settings and configuration (.env support)
│   ├── database.py          # SQLite connection setup
│   ├── models/              # SQLModel definitions
│   │   ├── __init__.py      # Model exports
│   │   ├── project.py       # Project model with CRUD schemas
│   │   └── repository.py    # Repository model with CRUD schemas
│   ├── internal/            # Internal business logic (Go-style)
│   │   ├── __init__.py      # Internal module init
│   │   ├── github.py        # GitHub API client with authentication
│   │   ├── parser.py        # Markdown parsing service (awesome list extraction)
│   │   ├── search.py        # MeiliSearch integration (skeleton)
│   │   └── sync.py          # Data synchronization orchestration
│   ├── routers/             # FastAPI route handlers
│   │   └── __init__.py      # Router setup
│   ├── templates/           # Jinja2 HTML templates
│   │   ├── base.html        # Base layout with HTMX/Alpine
│   │   ├── index.html       # Homepage with search interface
│   │   └── search_results.html # Search results partial
│   └── static/              # Self-hosted assets
│       ├── htmx.min.js      # HTMX library
│       └── alpine.min.js    # Alpine.js library
├── scripts/                 # Utility and data management scripts
│   ├── __init__.py          # Scripts package init
│   ├── seed_repositories.py # Repository seeding from sindresorhus/awesome
│   └── import_repositories.py # JSON backup import utility
├── .env                     # Environment configuration (GitHub token, DB path)
├── awesomesearch.db        # SQLite database file
├── awesome-repositories-backup.json # Repository data backup
├── pyproject.toml           # uv project configuration
├── uv.lock                  # Dependency lock file
└── CLAUDE.md               # This file
```

## Key Features

### Core Functionality
- **Repository Discovery**: Automatically find and validate Awesome repositories
- **Content Parsing**: Extract project entries from various markdown formats
- **Data Enrichment**: Fetch GitHub metadata (stars, language, last update)
- **Search Interface**: Fast, filtered search with HTMX live updates
- **Quality Scoring**: Rank projects by popularity and activity

### Technical Features
- **Type Safety**: Astral's ty type checker
- **SEO Friendly**: Server-side rendering with HTMX enhancement
- **Responsive Design**: Mobile-first interface

## Data Models

### Repository
- Awesome repository metadata (name, stars, description)
- Sync status and validation flags
- Activity tracking

### Project
- Individual project entries from Awesome lists
- Enriched with GitHub metadata
- Categorization and tagging
- Quality scoring metrics

## Development Workflow

### Setup
```bash
# Project already initialized with uv
# Dependencies: fastapi, sqlmodel, uvicorn, jinja2, httpx, pydantic-settings
# Dev dependencies: ruff, ty

# Set up environment variables
cp .env.example .env  # Configure GitHub token and database path

# To run the application:
uv run python -m app.main
```

### Data Management

```bash
# Seed database with awesome repositories
uv run python scripts/seed_repositories.py

# Import repositories from JSON backup
uv run python scripts/import_repositories.py awesome-repositories-backup.json

# Import with overwrite of existing repositories
uv run python scripts/import_repositories.py awesome-repositories-backup.json --overwrite
```

### Running
```bash
meilisearch &                    # Start search engine
uv run python -m app.main       # Start FastAPI server
```

### Code Quality
- **ruff** for linting and formatting
- **ty** for type checking
- **pytest** for testing (planned)
- Pre-commit hooks (planned)

## Deployment Strategy

### Phase 1: MVP
- Top 50 Awesome repositories
- Basic search functionality
- Simple web interface

### Phase 2: Enhancement
- All discoverable Awesome repos
- Advanced filtering and sorting
- Admin dashboard

### Phase 3: Scale
- Real-time updates via webhooks
- API for third-party integrations
- Community features

## Architecture Decisions

### Why This Stack?
- **HTMX over React**: Simpler deployment, better SEO, faster development
- **SQLite over PostgreSQL**: Easier setup, sufficient scale, simpler ops
- **MeiliSearch over Elasticsearch**: Better developer experience, faster setup
- **FastAPI over Django**: Better type safety, modern async support
- **uv over pip**: Faster dependency resolution and installation

### Key Design Principles
- **Simplicity First**: Minimal complexity, easy to understand and maintain
- **Type Safety**: Comprehensive type hints and validation
- **Performance**: Fast search, efficient data processing
- **Scalability**: Architecture supports growth without major rewrites

## Current Status

**Development Phase** - Data foundation complete, ready for search implementation:

✅ **Completed:**
- SQLModel data models (Repository, Project) with full CRUD schemas
- Internal services architecture (`app/internal/` Go-style organization)
- GitHub API client with authentication and rate limiting
- Markdown parser for extracting projects from awesome repository lists
- Repository seeding script that extracts 615+ awesome repositories from sindresorhus/awesome
- Database seeded with 30+ awesome repositories including metadata (stars, descriptions, etc.)
- Environment configuration system with .env support for GitHub tokens and database paths
- JSON backup/restore functionality for repository data
- HTMX/Alpine.js frontend with responsive templates
- Self-hosted static assets (HTMX, Alpine.js)
- FastAPI application structure with database setup

🚧 **In Progress:**
- MeiliSearch integration (service skeleton created)
- API routes for search and project endpoints
- Basic admin interface for repository management

📋 **Next Steps:**

- Complete MeiliSearch service implementation
- Create API routes for search and project endpoints
- Connect search API routes to HTMX frontend templates
- Add comprehensive error handling and logging
- Implement CLI commands for sync operations

## Data Status

- **Repository Database**: Seeded with 30+ awesome repositories from GitHub
- **Repository Backup**: JSON backup created at `awesome-repositories-backup.json`
- **Coverage**: Repositories include popular awesome lists (rust, iOS, hacking, etc.)
- **Next Phase**: Extract individual projects from these repositories' README files

## Lessons Learned

- **Database Path Issues**: Relative SQLite paths can cause databases to be created in unexpected locations when running
  scripts from different directories. Fixed by using absolute paths in .env configuration.
- **Import Order Matters**: When using path manipulation in scripts, ensure `sys.path` and `os.chdir()` are called
  before importing app modules to avoid engine creation with wrong working directory.
- **GitHub API**: Successfully integrated with proper authentication and handles rate limiting gracefully.
- **Markdown Parsing**: The awesome repository structure is consistent enough to extract repository URLs reliably with
  regex patterns.

## Domain

Target domain: **awesomeindex.dev**
