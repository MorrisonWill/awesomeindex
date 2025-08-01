# AwesomeIndex

> A fast, searchable index of GitHub's awesome lists

AwesomeIndex is a search engine for discovering curated open source projects across all of GitHub's "awesome"
repositories. AwesomeIndex indexes the actual projects within these lists, making it easy to search for tools or
libraries in various ecosystems.

## Features

- **Full-text search** across thousands of curated projects
- **Real-time filtering** by repository, category, language, and stars
- **Mobile-friendly** responsive design

## Technology Stack

- **Backend**: Python, FastAPI, SQLModel, SQLite
- **Search**: MeiliSearch
- **Frontend**: HTMX, Jinja2
- **Package Manager**: uv
- **Linting/Formatting**: Ruff
- **Type Checking**: Ty

## Getting Started

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- [MeiliSearch](https://www.meilisearch.com/) (v1.0+)
- GitHub personal access token (for API access)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/awesomeindex.git
cd awesomeindex
```

2. Install dependencies with uv:

```bash
uv sync
```

3. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your settings:
# - GITHUB_TOKEN: Your GitHub personal access token
# - DATABASE_URL: Path to SQLite database
# - MEILISEARCH_URL: MeiliSearch server URL (default: http://localhost:7700)
```

4. Start MeiliSearch:

```bash
# Using Docker
docker run -it --rm -p 7700:7700 getmeili/meilisearch:latest

# Or download and run the binary
curl -L https://install.meilisearch.com | sh
./meilisearch
```

5. Initialize the database and seed with repositories:

```bash
uv run python awesomeindex-seed
```

6. Parse projects from repositories:

```bash
uv run python awesomeindex-parse
```

7. Start the development server:

```bash
uv run python -m app.main
```

## CLI Commands

The project includes some CLI tools for managing data:

```bash
# Seed database with awesome repositories
uv run python cli.py seed

# Parse projects from repositories
uv run python cli.py parse

# Reindex all projects in MeiliSearch
uv run python cli.py reindex
```

## API Documentation

Once the server is running, visit:

- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc

## Contributing

Contributions are welcome! I believe this has the potential to be a valuable resource for developers.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [awesome](https://github.com/sindresorhus/awesome) - The awesome list of awesome lists
- [awesome-search](https://awesomelists.top/) - Another awesome list search engine
