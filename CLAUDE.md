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
│   ├── config.py            # Settings and configuration
│   ├── database.py          # SQLite connection setup
│   ├── models/              # SQLModel definitions
│   │   ├── __init__.py      # Model exports
│   │   ├── project.py       # Project model with CRUD schemas
│   │   └── repository.py    # Repository model with CRUD schemas
│   ├── internal/            # Internal business logic (Go-style)
│   │   ├── __init__.py      # Internal module init
│   │   ├── github.py        # GitHub API client
│   │   ├── parser.py        # Markdown parsing service
│   │   ├── search.py        # MeiliSearch integration
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
uv init
uv add fastapi sqlmodel uvicorn jinja2 httpx meilisearch-python-sdk
uv add --dev ruff ty
python scripts/setup.py
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

**Development Phase** - Core architecture implemented with:

✅ **Completed:**
- SQLModel data models (Repository, Project) with full CRUD schemas
- Internal services architecture (`app/internal/` Go-style organization)
- GitHub API client with repository discovery and README fetching
- Markdown parser for extracting projects from awesome lists
- Data synchronization service combining GitHub + parser + search
- HTMX/Alpine.js frontend with responsive templates
- Self-hosted static assets (HTMX, Alpine.js)
- FastAPI application structure with database setup

🚧 **In Progress:**
- MeiliSearch integration (service skeleton created)
- API routes for search and project endpoints
- Basic admin interface for repository management

📋 **Next Steps:**
- Complete search service implementation
- Add API routes and connect to frontend
- Create data seeding scripts for testing
- Add error handling and logging
- Implement CLI commands for sync operations

## Domain

Target domain: **awesomeindex.dev**
