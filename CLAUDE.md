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
- **MeiliSearch** - Search engine with meilisearch-python-sdk (async client)
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
│   │   ├── __init__.py      # Router setup
│   │   ├── search.py        # Search API endpoints
│   │   └── projects.py      # Project API endpoints
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
│   ├── import_repositories.py # JSON backup import utility
│   ├── parse_projects.py    # Parse projects from repository READMEs and index in MeiliSearch
│   └── test_search.py       # Test MeiliSearch functionality
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
- **Content Parsing**: Extract project entries from various markdown formats using regex patterns
- **Full-Text Search**: MeiliSearch-powered search with typo tolerance and instant results
- **Search Interface**: Real-time search with HTMX (300ms delay) and category/repository filtering
- **REST API**: Complete API for search, project browsing, and metadata retrieval
- **Data Enrichment**: Fetch GitHub metadata (stars, language, last update) - planned

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

## API Endpoints

### Search API (`/api/search/`)

- `GET /api/search/?q={query}&category={category}&repository={repository}&limit={limit}&offset={offset}` - Search
  projects with filtering
- `GET /api/search/stats` - Get search index statistics
- `POST /api/search/reindex` - Re-index all projects (admin)

### Project API (`/api/projects/`)

- `GET /api/projects/` - List all projects with optional filtering
- `GET /api/projects/{id}` - Get specific project by ID
- `GET /api/projects/repository/{repository_id}` - Get projects from specific repository
- `GET /api/projects/categories/` - Get all unique categories
- `GET /api/projects/repositories/` - Get all repositories with projects

### Frontend Routes

- `GET /` - Homepage with search interface
- `GET /search?q={query}&category={category}&repository={repository}` - Search results (returns HTML for HTMX)

## Development Workflow

### Setup
```bash
# Project already initialized with uv
# Dependencies: fastapi, sqlmodel, uvicorn, jinja2, httpx, pydantic-settings, meilisearch-python-sdk
# Dev dependencies: ruff, ty

# Set up environment variables
cp .env.example .env  # Configure GitHub token and database path

# To run the application:
uv run python -m app.main
```


### Running
```bash
meilisearch &                    # Start search engine
uv run python -m app.main       # Start FastAPI server
```

### CLI Commands

```bash
# Seed database with awesome repositories
uv run python cli.py seed

# Parse projects from repositories and index in MeiliSearch  
uv run python cli.py parse 5

# Test search functionality
uv run python cli.py test
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

**Production Ready MVP** - Full search functionality implemented and working:

✅ **Completed:**
- SQLModel data models (Repository, Project) with full CRUD schemas
- Internal services architecture (`app/internal/` Go-style organization)
- GitHub API client with authentication and rate limiting
- Markdown parser for extracting projects from awesome repository lists
- Repository seeding script that extracts 615+ awesome repositories from sindresorhus/awesome
- Database seeded with 30+ awesome repositories including metadata (stars, descriptions, etc.)
- Environment configuration system with .env support for GitHub tokens and database paths
- JSON backup/restore functionality for repository data
- **MeiliSearch integration with async client** - Full search service implementation
- **Project parsing and indexing** - 559 projects parsed and indexed from 3 repositories
- **Complete API routes** - Search, projects, categories, and repositories endpoints
- **HTMX frontend integration** - Real-time search with filtering and responsive UI
- Self-hosted static assets (HTMX, Alpine.js)
- FastAPI application structure with database setup and search initialization

📋 **Next Steps:**
- Add comprehensive error handling and logging
- Implement CLI commands for sync operations
- Parse projects from all 30+ repositories in database
- Add pagination for large result sets
- Create admin interface for repository management
- Add project metadata enrichment (GitHub stars, languages)
- Implement caching strategies for frequently searched terms

## Data Status

- **Repository Database**: Seeded with 30+ awesome repositories from GitHub
- **Repository Backup**: JSON backup created at `awesome-repositories-backup.json`
- **Project Database**: 559 individual projects parsed and stored from 3 repositories:
    - awesome-conversational-ai (33 projects)
    - awesome-microservices (444 projects)
    - awesome-playwright (82 projects)
- **Search Index**: All 559 projects indexed in MeiliSearch with full-text search capabilities
- **Coverage**: Repositories include popular awesome lists (conversational-ai, microservices, playwright, etc.)
- **API Endpoints**: Fully functional search and project browsing via REST API
- **Web Interface**: Live search interface at http://localhost:8000 with category/repository filtering

## Lessons Learned

### Database & Path Management

- **Database Path Issues**: Relative SQLite paths can cause databases to be created in unexpected locations when running
  scripts from different directories. Fixed by using absolute paths in .env configuration.
- **Import Order Matters**: When using path manipulation in scripts, ensure `sys.path` and `os.chdir()` are called
  before importing app modules to avoid engine creation with wrong working directory.

### External Integrations
- **GitHub API**: Successfully integrated with proper authentication and handles rate limiting gracefully.
- **MeiliSearch SDK**: The meilisearch-python-sdk provides excellent async support for FastAPI. Key learnings:
    - Use AsyncClient for async operations with FastAPI
    - MeiliSearch response objects have different attribute names than expected (e.g., `estimated_total_hits` vs
      `nb_hits`)
    - Index configuration (searchable, filterable, sortable attributes) must be applied after index creation
    - Error handling is crucial as network operations can fail

### Data Processing

- **Markdown Parsing**: The awesome repository structure is consistent enough to extract repository URLs reliably with
  regex patterns.
- **Project Extraction**: Successfully parsed 559 projects from 3 repositories with consistent structure:
    - List items with `[Name](URL) - Description` format are most common
    - Category headers help organize projects by functionality
    - Some inconsistencies in formatting but parser handles most variations

### Frontend Development

- **HTMX Integration**: HTMX works excellently for real-time search with minimal JavaScript:
    - 300ms delay prevents excessive API calls during typing
    - Server-side rendering keeps SEO benefits while adding interactivity
    - Filter dropdowns populated via vanilla JavaScript and API calls
- **CSS Styling**: Custom CSS with flexbox provides responsive design without frameworks

### Performance

- **Search Performance**: MeiliSearch provides sub-millisecond search across 559 documents
- **Database Operations**: SQLite performs well for current scale with proper indexing on foreign keys and search fields

## Domain

Target domain: **awesomeindex.dev**
